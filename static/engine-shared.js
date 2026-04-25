/* ========================================================
   Veyrafish 引擎页共享 JS 工具
   所有引擎页均引用此文件，不可删除
   ======================================================== */

// ---- 全局常量 ----
const CONFIG_ENDPOINT = '/api/config';
const SYSTEM_STATUS_ENDPOINT = '/api/system/status';
const SYSTEM_START_ENDPOINT = '/api/system/start';
const SYSTEM_SHUTDOWN_ENDPOINT = '/api/system/shutdown';
const START_BUTTON_DEFAULT_TEXT = '保存并启动系统';

// ---- 全局状态 ----
let socket;
let socketConnected = false;
let backendReachable = false;
let systemStarted = false;
let systemStarting = false;
let shutdownInProgress = false;
let pageRefreshInProgress = false;
let configDirty = false;
let configModalLocked = false;
let configAutoRefreshTimer = null;
let configValues = {};
let connectionProbeTimer = null;
const CONNECTION_PROBE_INTERVAL = 15000;

// appStatus – 各引擎页仅 track 本页关心的引擎
let appStatus = { insight:'stopped', media:'stopped', query:'stopped', forum:'stopped', report:'stopped' };

// ---- 简单控制台 ----
function getConsoleOutput() { return document.getElementById('engineConsole'); }

function appendLog(text, cls) {
    const container = getConsoleOutput();
    if (!container) return;
    const line = document.createElement('div');
    line.className = 'console-line' + (cls ? ' ' + cls : '');
    line.textContent = text;
    container.appendChild(line);
    container.scrollTop = container.scrollHeight;
}

function clearConsole(message) {
    const container = getConsoleOutput();
    if (!container) return;
    container.innerHTML = '';
    if (message) appendLog(message);
}

// ---- Socket.IO 初始化 ----
function initEngineSocket(engineName) {
    if (typeof io === 'undefined') return;
    socket = io();

    socket.on('connect', function () {
        socketConnected = true;
        refreshConnectionStatus();
    });

    socket.on('disconnect', function () {
        socketConnected = false;
        refreshConnectionStatus();
    });

    socket.on('console_output', function (data) {
        if (!engineName || data.app === engineName) {
            appendLog(data.line || '');
        }
    });

    socket.on('status_update', function (data) {
        updateAppStatus(data);
    });
}

// ---- 状态检查 ----
function checkStatus() {
    fetch('/api/status')
        .then(r => r.json())
        .then(data => {
            backendReachable = true;
            updateAppStatus(data);
            refreshConnectionStatus();
        })
        .catch(() => {
            backendReachable = false;
            refreshConnectionStatus();
        });
}

function updateAppStatus(data) {
    for (const [app, info] of Object.entries(data)) {
        const status = info.status === 'running' ? 'running' : 'stopped';
        appStatus[app] = status;
        const el = document.getElementById('status-' + app);
        if (el) el.className = 'status-indicator ' + status;
    }
}

function refreshConnectionStatus() {
    const el = document.getElementById('connectionStatus');
    if (!el) return;
    if (socketConnected || backendReachable) {
        el.textContent = '已连接';
    } else {
        el.textContent = '连接断开';
    }
}

function updateTime() {
    const el = document.getElementById('systemTime');
    if (el) el.textContent = new Date().toLocaleTimeString('zh-CN');
}

// ---- 消息提示 ----
function showMessage(text, type) {
    type = type || 'info';
    const msg = document.getElementById('message');
    if (!msg) return;
    if (msg.hideTimer) clearTimeout(msg.hideTimer);
    msg.textContent = text;
    msg.className = 'message ' + type;
    msg.classList.add('show');
    msg.hideTimer = setTimeout(function () {
        msg.classList.remove('show');
        setTimeout(function () { msg.textContent = ''; msg.className = 'message'; }, 300);
    }, 3000);
}

// ---- 系统菜单 ----
function initUtilityMenu() {
    const trigger = document.getElementById('utilityMenuTrigger');
    const popover = document.getElementById('utilityMenuPopover');
    const closeBtn = document.getElementById('utilityMenuClose');
    const root = document.getElementById('utilityMenu');
    if (!trigger || !popover || !root) return;

    function setOpen(open) {
        if (open) { popover.classList.add('visible'); trigger.setAttribute('aria-expanded', 'true'); }
        else { popover.classList.remove('visible'); trigger.setAttribute('aria-expanded', 'false'); }
    }
    function isOpen() { return popover.classList.contains('visible'); }

    trigger.addEventListener('click', function (e) { e.preventDefault(); setOpen(!isOpen()); });
    if (closeBtn) closeBtn.addEventListener('click', function () { setOpen(false); });
    document.addEventListener('click', function (e) {
        if (!isOpen()) return;
        if (!root.contains(e.target)) setOpen(false);
    });
    document.addEventListener('keydown', function (e) {
        if (!isOpen()) return;
        if (e.key === 'Escape') { setOpen(false); trigger.focus(); }
    });
}

// ---- 安全刷新 ----
async function handleSafeRefresh() {
    if (pageRefreshInProgress) return;
    pageRefreshInProgress = true;
    const btn = document.getElementById('pageRefreshButton');
    const orig = btn ? btn.textContent : '';
    if (btn) { btn.disabled = true; btn.textContent = '刷新中...'; }
    try {
        await fetchSystemStatus();
        await checkStatus();
        showMessage('已刷新最新状态', 'success');
    } catch (e) {
        showMessage('刷新失败: ' + e.message, 'error');
    } finally {
        pageRefreshInProgress = false;
        if (btn) { btn.disabled = false; btn.textContent = orig || '刷新界面'; }
    }
}

// ---- 关机流程 ----
function getRunningAgents() {
    return Object.keys(appStatus).filter(function (a) { return appStatus[a] === 'running'; });
}

function hideShutdownConfirm() {
    const m = document.getElementById('shutdownConfirmModal');
    if (m) { m.classList.remove('visible'); m.setAttribute('aria-hidden', 'true'); }
}

function showShutdownConfirm(runningAgents) {
    const m = document.getElementById('shutdownConfirmModal');
    const st = document.getElementById('shutdownStrongText');
    const portList = document.getElementById('shutdownPortList');

    if (st) st.textContent = (runningAgents && runningAgents.length > 0) ? '部分引擎正在运行，确定关闭？' : '确定要关闭系统吗？';

    if (portList) {
        const items = Object.keys(appStatus).map(function (k) {
            const running = appStatus[k] === 'running';
            return '<span class="confirm-pill shutdown-pill">' + k + ' · ' + (running ? '运行中' : '未运行') + '</span>';
        });
        portList.innerHTML = items.join('') || '<span class="confirm-pill">暂无运行中的引擎</span>';
    }
    if (m) { m.classList.add('visible'); m.setAttribute('aria-hidden', 'false'); }
}

function handleShutdownRequest() {
    if (shutdownInProgress) return;
    if (systemStarting) { showMessage('系统正在启动，请稍后关闭', 'error'); return; }
    const running = getRunningAgents();
    if (running.length > 0) { showShutdownConfirm(running); return; }
    shutdownSystem({ skipAgentWarning: true });
}

async function shutdownSystem(options) {
    options = options || {};
    if (shutdownInProgress) return;
    if (!options.skipAgentWarning) {
        const running = getRunningAgents();
        if (running.length > 0) { showShutdownConfirm(running); return; }
    }
    shutdownInProgress = true;
    const btn = document.getElementById('shutdownButton');
    const orig = btn ? btn.textContent : '';
    if (btn) { btn.disabled = true; btn.textContent = '关闭中...'; }
    try {
        const ctrl = new AbortController();
        const tid = setTimeout(function () { ctrl.abort(); }, 4000);
        const resp = await fetch(SYSTEM_SHUTDOWN_ENDPOINT, { method: 'POST', signal: ctrl.signal });
        clearTimeout(tid);
        if (!resp.ok) throw new Error('服务返回 ' + resp.status);
        showMessage('系统正在停止，请稍候...', 'success');
    } catch (e) {
        const txt = e.name === 'AbortError' ? '停止指令已发送，请稍候退出' : '停止失败: ' + e.message;
        showMessage(txt, e.name === 'AbortError' ? 'success' : 'error');
        if (e.name !== 'AbortError') {
            shutdownInProgress = false;
            if (btn) { btn.disabled = false; btn.textContent = orig || '关闭系统'; }
        }
    }
}

// ---- 系统状态 ----
async function fetchSystemStatus() {
    try {
        const resp = await fetch(SYSTEM_STATUS_ENDPOINT);
        const data = await resp.json();
        if (data && data.success) applySystemState(data);
        return data;
    } catch (e) { console.error('获取系统状态失败', e); return null; }
}

function applySystemState(state) {
    if (!state) return;
    if (state.hasOwnProperty('started')) systemStarted = !!state.started;
    if (state.hasOwnProperty('starting')) systemStarting = !!state.starting;
    updateStartButtonState();
    updateConfigCloseButton();
}

async function ensureSystemReady() {
    const status = await fetchSystemStatus();
    if (!status || !status.success) {
        openConfigModal({ lock: true, message: '无法获取系统状态，请检查配置后重试。' });
        return;
    }
    if (!status.started) {
        openConfigModal({ lock: true, message: '请先确认配置，然后点击"保存并启动系统"' });
    } else {
        applySystemState(status);
        configModalLocked = false;
    }
}

// ---- 配置弹窗 ----
const configFieldGroups = [
    {
        title: '数据库配置',
        subtitle: '配置 PostgreSQL / MySQL 连接信息',
        fields: [
            { key: 'DB_DIALECT', label: '数据库类型', type: 'select', options: ['postgresql', 'mysql'] },
            { key: 'DB_HOST', label: '主机地址' },
            { key: 'DB_PORT', label: '端口', type: 'number' },
            { key: 'DB_USER', label: '用户名' },
            { key: 'DB_PASSWORD', label: '密码', type: 'password' },
            { key: 'DB_NAME', label: '数据库名' }
        ]
    },
    {
        title: 'Insight Agent',
        subtitle: 'OpenAi接入格式，推荐LLM：kimi-k2',
        fields: [
            { key: 'INSIGHT_ENGINE_API_KEY', label: 'API Key', type: 'password' },
            { key: 'INSIGHT_ENGINE_BASE_URL', label: 'Base URL' },
            { key: 'INSIGHT_ENGINE_MODEL_NAME', label: '模型名称' }
        ]
    },
    {
        title: 'Media Agent',
        subtitle: 'OpenAi接入格式，推荐LLM：gemini-2.5-pro',
        fields: [
            { key: 'MEDIA_ENGINE_API_KEY', label: 'API Key', type: 'password' },
            { key: 'MEDIA_ENGINE_BASE_URL', label: 'Base URL' },
            { key: 'MEDIA_ENGINE_MODEL_NAME', label: '模型名称' }
        ]
    },
    {
        title: 'Query Agent',
        subtitle: 'OpenAi接入格式，推荐LLM：deepseek-chat',
        fields: [
            { key: 'QUERY_ENGINE_API_KEY', label: 'API Key', type: 'password' },
            { key: 'QUERY_ENGINE_BASE_URL', label: 'Base URL' },
            { key: 'QUERY_ENGINE_MODEL_NAME', label: '模型名称' }
        ]
    },
    {
        title: 'Report Agent',
        subtitle: 'OpenAi接入格式，推荐LLM：gemini-2.5-pro',
        fields: [
            { key: 'REPORT_ENGINE_API_KEY', label: 'API Key', type: 'password' },
            { key: 'REPORT_ENGINE_BASE_URL', label: 'Base URL' },
            { key: 'REPORT_ENGINE_MODEL_NAME', label: '模型名称' }
        ]
    },
    {
        title: 'Forum Host',
        subtitle: 'OpenAi接入格式，推荐LLM：qwen-plus',
        fields: [
            { key: 'FORUM_HOST_API_KEY', label: 'API Key', type: 'password' },
            { key: 'FORUM_HOST_BASE_URL', label: 'Base URL' },
            { key: 'FORUM_HOST_MODEL_NAME', label: '模型名称' }
        ]
    },
    {
        title: '外部检索工具',
        subtitle: '联动搜索引擎、网站抓取等在线服务',
        fields: [
            { key: 'SEARCH_TOOL_TYPE', label: '选择检索工具', type: 'select', options: ['BochaAPI', 'AnspireAPI'] },
            { key: 'TAVILY_API_KEY', label: 'Tavily API Key', type: 'password' },
            { key: 'BOCHA_WEB_SEARCH_API_KEY', label: 'Bocha API Key', type: 'password', condition: { key: 'SEARCH_TOOL_TYPE', value: 'BochaAPI' } },
            { key: 'ANSPIRE_API_KEY', label: 'Anspire API Key', type: 'password', condition: { key: 'SEARCH_TOOL_TYPE', value: 'AnspireAPI' } }
        ]
    }
];

function escapeHtml(s) {
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}

function renderConfigForm(values) {
    const container = document.getElementById('configFormContainer');
    if (!container) return;
    const eyeOff = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>`;

    const sections = configFieldGroups.map(function (group) {
        const fieldsHtml = group.fields.map(function (field) {
            const value = (values && values[field.key] !== undefined) ? values[field.key] : '';
            const sv = escapeHtml(String(value || ''));
            let hidden = '';
            if (field.condition) {
                const cv = values && values[field.condition.key];
                if (cv !== field.condition.value) hidden = ' hidden';
            }
            let control;
            if (field.type === 'select' && field.options) {
                const opts = field.options.map(function (o) {
                    return '<option value="' + escapeHtml(o) + '"' + (o === value ? ' selected' : '') + '>' + escapeHtml(o) + '</option>';
                }).join('');
                control = '<select class="config-field-input" data-config-key="' + field.key + '" data-field-type="select">' + opts + '</select>';
            } else if (field.type === 'password') {
                control = '<div class="config-password-wrapper"><input type="password" class="config-field-input" data-config-key="' + field.key + '" data-field-type="password" value="' + sv + '" placeholder="填写' + escapeHtml(field.label) + '" autocomplete="off"><button type="button" class="config-password-toggle" data-target="' + field.key + '">' + eyeOff + '</button></div>';
            } else {
                const t = field.type || 'text';
                control = '<input type="' + t + '" class="config-field-input" data-config-key="' + field.key + '" data-field-type="' + t + '" value="' + sv + '" placeholder="填写' + escapeHtml(field.label) + '" autocomplete="on">';
            }
            const condKey = field.condition ? field.condition.key : '';
            const condVal = field.condition ? field.condition.value : '';
            return '<label class="config-field' + hidden + '" data-condition-key="' + condKey + '" data-condition-value="' + condVal + '"><span class="config-field-label">' + escapeHtml(field.label) + '</span>' + control + '</label>';
        }).join('');
        const sub = group.subtitle ? '<div class="config-group-subtitle">' + escapeHtml(group.subtitle) + '</div>' : '';
        return '<section class="config-group"><div class="config-group-title">' + escapeHtml(group.title) + '</div>' + sub + fieldsHtml + '</section>';
    }).join('');

    container.innerHTML = sections;
    attachConditionalLogic(container);
}

function attachPasswordToggles(container) {
    const eyeOff = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>`;
    const eyeOn = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>`;
    if (container.dataset.pwAttached) return;
    container.dataset.pwAttached = 'true';
    container.addEventListener('click', function (e) {
        const toggle = e.target.closest('.config-password-toggle');
        if (!toggle) return;
        const key = toggle.dataset.target;
        const input = container.querySelector('.config-field-input[data-config-key="' + key + '"]');
        if (!input) return;
        const reveal = input.getAttribute('type') === 'password';
        input.setAttribute('type', reveal ? 'text' : 'password');
        toggle.innerHTML = reveal ? eyeOn : eyeOff;
        toggle.classList.toggle('revealed', reveal);
    });
}

function attachConditionalLogic(container) {
    if (container.dataset.condLogicAttached) return;
    container.dataset.condLogicAttached = 'true';
    container.addEventListener('change', function (e) {
        const sel = e.target.closest('select.config-field-input');
        if (!sel) return;
        const trigKey = sel.dataset.configKey;
        const trigVal = sel.value;
        container.querySelectorAll('.config-field[data-condition-key]').forEach(function (f) {
            if (f.dataset.conditionKey === trigKey) {
                f.classList.toggle('hidden', trigVal !== f.dataset.conditionValue);
            }
        });
    });
}

function collectConfigUpdates() {
    const updates = {};
    document.querySelectorAll('#configFormContainer [data-config-key]').forEach(function (input) {
        const key = input.dataset.configKey;
        if (!key) return;
        let val = input.value;
        if (input.dataset.fieldType !== 'password' && typeof val === 'string') val = val.trim();
        if (val !== '' && /PORT$/i.test(key)) {
            const n = Number(val);
            if (!isNaN(n)) { updates[key] = n; return; }
        }
        updates[key] = val;
    });
    return updates;
}

function setConfigStatus(msg, type) {
    const el = document.getElementById('configStatusMessage');
    if (!el) return;
    el.textContent = msg || '';
    el.classList.remove('error', 'success');
    if (type) el.classList.add(type);
}

function updateStartButtonState() {
    const btn = document.getElementById('startSystemButton');
    if (!btn) return;
    if (systemStarting) { btn.disabled = true; btn.textContent = '启动中...'; }
    else if (systemStarted) { btn.disabled = true; btn.textContent = '系统已启动'; }
    else { btn.disabled = false; btn.textContent = START_BUTTON_DEFAULT_TEXT; }
}

function updateConfigCloseButton() {
    const btn = document.getElementById('closeConfigModal');
    if (!btn) return;
    if (configModalLocked && !systemStarted) btn.setAttribute('disabled', 'disabled');
    else btn.removeAttribute('disabled');
}

function isConfigModalVisible() {
    const m = document.getElementById('configModal');
    return m ? m.classList.contains('visible') : false;
}

function openConfigModal(options) {
    options = options || {};
    const { lock = false, message = '' } = options;
    const m = document.getElementById('configModal');
    if (!m) return;
    configModalLocked = lock;
    m.classList.add('visible');
    configDirty = false;
    setConfigStatus(message || '正在读取配置...');
    refreshConfigFromServer(true, message || '');
    if (configAutoRefreshTimer) clearInterval(configAutoRefreshTimer);
    configAutoRefreshTimer = setInterval(function () {
        if (!configDirty) refreshConfigFromServer(false, '');
    }, 10000);
    updateStartButtonState();
    updateConfigCloseButton();
}

function closeConfigModal(force) {
    if (!force && configModalLocked && !systemStarted) {
        setConfigStatus('请先完成配置并启动系统', 'error');
        showMessage('请先完成配置并启动系统', 'error');
        return;
    }
    const m = document.getElementById('configModal');
    if (m) m.classList.remove('visible');
    if (configAutoRefreshTimer) { clearInterval(configAutoRefreshTimer); configAutoRefreshTimer = null; }
    configDirty = false;
    configModalLocked = false;
    setConfigStatus('');
    updateStartButtonState();
    updateConfigCloseButton();
}

function refreshConfigFromServer(showFeedback, messageOverride) {
    if (showFeedback && configDirty) {
        if (!window.confirm('当前修改尚未保存，确定要刷新并放弃更改吗？')) return;
    }
    fetch(CONFIG_ENDPOINT)
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (!data.success) throw new Error(data.message || '读取配置失败');
            configValues = data.config || {};
            renderConfigForm(configValues);
            const container = document.getElementById('configFormContainer');
            if (container) attachPasswordToggles(container);
            configDirty = false;
            if (messageOverride) setConfigStatus(messageOverride);
            else if (showFeedback) setConfigStatus('已加载最新配置');
            else setConfigStatus('已同步最新配置');
        })
        .catch(function (e) { setConfigStatus('读取配置失败: ' + e.message, 'error'); });
}

async function saveConfigUpdates(options) {
    options = options || {};
    const silent = options.silent || false;
    const btn = document.getElementById('saveConfigButton');
    if (!silent && btn) { btn.disabled = true; btn.textContent = '保存中...'; }
    if (!silent) setConfigStatus('正在保存配置...');
    const updates = collectConfigUpdates();
    try {
        const resp = await fetch(CONFIG_ENDPOINT, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updates)
        });
        const data = await resp.json();
        if (!data.success) throw new Error(data.message || '保存失败');
        configValues = data.config || {};
        renderConfigForm(configValues);
        configDirty = false;
        setConfigStatus('配置已保存', 'success');
        if (!silent) showMessage('配置已保存', 'success');
        return true;
    } catch (e) {
        setConfigStatus('保存失败: ' + e.message, 'error');
        if (!silent) showMessage('保存失败: ' + e.message, 'error');
        return false;
    } finally {
        if (!silent && btn) { btn.disabled = false; btn.textContent = '保存'; }
    }
}

async function startSystem() {
    if (systemStarting) { setConfigStatus('系统正在启动，请稍候...'); return; }
    systemStarting = true;
    updateStartButtonState();
    try {
        if (configDirty) {
            setConfigStatus('检测到未保存的修改，正在保存...');
            const saved = await saveConfigUpdates({ silent: true });
            if (!saved) { systemStarting = false; updateStartButtonState(); return; }
        }
        setConfigStatus('正在启动系统...');
        const resp = await fetch(SYSTEM_START_ENDPOINT, { method: 'POST' });
        const data = await resp.json();
        if (!resp.ok || !data.success) throw new Error(data && data.message ? data.message : '系统启动失败');
        showMessage('系统启动成功', 'success');
        setConfigStatus('系统启动成功', 'success');
        applySystemState({ started: true, starting: false });
        configModalLocked = false;
        setTimeout(function () { closeConfigModal(); }, 800);
        setTimeout(function () { checkStatus(); }, 1000);
        setTimeout(function () { window.location.reload(); }, 1200);
    } catch (e) {
        setConfigStatus('系统启动失败: ' + e.message, 'error');
        showMessage('系统启动失败: ' + e.message, 'error');
        applySystemState({ started: false, starting: false });
    } finally {
        systemStarting = false;
        updateStartButtonState();
        await fetchSystemStatus();
    }
}

// ---- 通用事件绑定 ----
function bindSharedListeners() {
    const openCfg = document.getElementById('openConfigButton');
    if (openCfg) openCfg.addEventListener('click', function () { openConfigModal({ lock: !systemStarted }); });

    const closeCfg = document.getElementById('closeConfigModal');
    if (closeCfg) closeCfg.addEventListener('click', function () { closeConfigModal(); });

    const refreshCfg = document.getElementById('refreshConfigButton');
    if (refreshCfg) refreshCfg.addEventListener('click', function () { refreshConfigFromServer(true, ''); });

    const saveCfg = document.getElementById('saveConfigButton');
    if (saveCfg) saveCfg.addEventListener('click', function () { saveConfigUpdates(); });

    const startBtn = document.getElementById('startSystemButton');
    if (startBtn) startBtn.addEventListener('click', function () { startSystem(); });

    const refreshPage = document.getElementById('pageRefreshButton');
    if (refreshPage) refreshPage.addEventListener('click', function () { handleSafeRefresh(); });

    const shutdownBtn = document.getElementById('shutdownButton');
    if (shutdownBtn) shutdownBtn.addEventListener('click', function () { handleShutdownRequest(); });

    const cancelShutdown = document.getElementById('cancelShutdownButton');
    if (cancelShutdown) cancelShutdown.addEventListener('click', function () { hideShutdownConfirm(); });

    const closeShutdown = document.getElementById('closeShutdownConfirm');
    if (closeShutdown) closeShutdown.addEventListener('click', function () { hideShutdownConfirm(); });

    const confirmShutdown = document.getElementById('confirmShutdownButton');
    if (confirmShutdown) confirmShutdown.addEventListener('click', function () {
        hideShutdownConfirm();
        shutdownSystem({ skipAgentWarning: true });
    });

    const cfgModal = document.getElementById('configModal');
    if (cfgModal) cfgModal.addEventListener('click', function (e) {
        if (e.target === cfgModal) closeConfigModal();
    });

    const cfgForm = document.getElementById('configFormContainer');
    if (cfgForm) cfgForm.addEventListener('input', function () {
        configDirty = true;
        setConfigStatus('已修改，尚未保存');
    });

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            if (isConfigModalVisible()) closeConfigModal();
            const sm = document.getElementById('shutdownConfirmModal');
            if (sm && sm.classList.contains('visible')) hideShutdownConfirm();
        }
    });
}

// ---- Connection probe ----
function startConnectionProbe() {
    if (connectionProbeTimer) clearInterval(connectionProbeTimer);
    probeConnection();
    connectionProbeTimer = setInterval(probeConnection, CONNECTION_PROBE_INTERVAL);
}

function probeConnection() {
    fetch('/api/report/status?heartbeat=1', { cache: 'no-store' })
        .then(function (r) {
            if (!r.ok) throw new Error();
            return r.json();
        })
        .then(function () { backendReachable = true; refreshConnectionStatus(); })
        .catch(function () { backendReachable = false; refreshConnectionStatus(); });
}
