"""
日志监控器 - 实时监控三个log文件中的SummaryNode输出
"""

import os
import time
import threading
from pathlib import Path
from datetime import datetime
import re
import json
from typing import Dict, Optional, List
from threading import Lock
from loguru import logger

# 导入论坛主持人模块
try:
    from .llm_host import generate_host_speech
    HOST_AVAILABLE = True
except ImportError:
    logger.exception("ForumEngine: 论坛主持人模块未找到，将以纯监控模式运行")
    HOST_AVAILABLE = False

# 可选：向 task_store 写入 Forum 进度事件
try:
    from task_store import get_task_store as _get_task_store
    _TASK_STORE_AVAILABLE = True
except Exception:
    _TASK_STORE_AVAILABLE = False
    _get_task_store = None  # type: ignore

class LogMonitor:
    """基于文件变化的智能日志监控器"""
   
    def __init__(self, log_dir: str = "logs"):
        """初始化日志监控器"""
        self.log_dir = Path(log_dir)
        self.forum_log_file = self.log_dir / "forum.log"
       
        # 要监控的日志文件
        self.monitored_logs = {
            'insight': self.log_dir / 'insight.log',
            'media': self.log_dir / 'media.log',
            'query': self.log_dir / 'query.log'
        }
       
        # 监控状态
        self.is_monitoring = False
        self.monitor_thread = None
        self.file_positions = {}  # 记录每个文件的读取位置
        self.file_line_counts = {}  # 记录每个文件的行数
        self.is_searching = False  # 是否正在搜索
        self.search_inactive_count = 0  # 搜索非活跃计数器
        self.write_lock = Lock()  # 写入锁，防止并发写入冲突
        
        # 主持人相关状态
        self.agent_speeches_buffer = []  # agent发言缓冲区
        self.host_speech_threshold = 5  # 每5条agent发言触发一次主持人发言
        self.is_host_generating = False  # 主持人是否正在生成发言
       
        # 目标节点识别模式
        # 1. 类名（旧格式可能包含）
        # 2. 完整模块路径（实际日志格式，包含引擎前缀）
        # 3. 部分模块路径（兼容性）
        # 4. 关键标识文本
        self.target_node_patterns = [
            'FirstSummaryNode',  # 类名
            'ReflectionSummaryNode',  # 类名
            'InsightEngine.nodes.summary_node',  # InsightEngine完整路径
            'MediaEngine.nodes.summary_node',  # MediaEngine完整路径
            'QueryEngine.nodes.summary_node',  # QueryEngine完整路径
            'nodes.summary_node',  # 模块路径（兼容性，用于部分匹配）
            '正在生成首次段落总结',  # FirstSummaryNode的标识
            '正在生成反思总结',  # ReflectionSummaryNode的标识
        ]
        
        # 多行内容捕获状态
        self.capturing_json = {}  # 每个app的JSON捕获状态
        self.json_buffer = {}     # 每个app的JSON缓冲区
        self.json_start_line = {} # 每个app的JSON开始行
        self.in_error_block = {}  # 每个app是否在ERROR块中
       
        # 确保logs目录存在
        self.log_dir.mkdir(exist_ok=True)

        # 进度事件：可选绑定一个 task_id 用于写入 task_events 表
        self.task_id: Optional[str] = None
        # Forum 内部统计：已收到的 agent 发言数、主持人触发次数
        self._forum_speech_count: int = 0
        self._host_trigger_count: int = 0
        self._force_host_from_events: bool = False
   
    def bind_task(self, task_id: Optional[str]) -> None:
        """绑定一个 task_id，用于向 task_store 写入 Forum 进度事件。"""
        self.task_id = task_id
        self._forum_speech_count = 0
        self._host_trigger_count = 0
        if task_id:
            logger.info(f"ForumEngine: 已绑定 task_id={task_id[:8]}...")

    def _emit(
        self,
        event_type: str,
        node_name: Optional[str] = None,
        detail: Optional[dict] = None,
    ) -> None:
        """向 task_store 写入 Forum 进度事件；无 task_id 或不可用时静默跳过。"""
        if not self.task_id or not _TASK_STORE_AVAILABLE:
            return
        try:
            store = _get_task_store()
            store.add_event(
                task_id=self.task_id,
                event_type=event_type,
                node_name=node_name,
                detail=detail,
            )
        except Exception as exc:  # pragma: no cover
            logger.warning(f"ForumEngine: 写入进度事件失败，忽略继续: {exc}")

    def clear_forum_log(self):
        """清空forum.log文件"""
        try:
            if self.forum_log_file.exists():
                self.forum_log_file.unlink()
           
            # 创建新的forum.log文件并写入开始标记
            start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # 使用write_to_forum_log函数来写入开始标记，确保格式一致
            with open(self.forum_log_file, 'w', encoding='utf-8') as f:
                pass  # 先创建空文件
            self.write_to_forum_log(f"=== ForumEngine 监控开始 - {start_time} ===", "SYSTEM")
               
            logger.info(f"ForumEngine: forum.log 已清空并初始化")
            
            # 重置JSON捕获状态
            self.capturing_json = {}
            self.json_buffer = {}
            self.json_start_line = {}
            self.in_error_block = {}
            
            # 重置主持人相关状态
            self.agent_speeches_buffer = []
            self.is_host_generating = False
           
        except Exception as e:
            logger.exception(f"ForumEngine: 清空forum.log失败: {e}")
   
    def write_to_forum_log(self, content: str, source: str = None):
        """写入内容到forum.log（线程安全）"""
        try:
            with self.write_lock:  # 使用锁确保线程安全
                with open(self.forum_log_file, 'a', encoding='utf-8') as f:
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    # 将内容中的实际换行符转换为\n字符串，确保整个记录在一行
                    content_one_line = content.replace('\n', '\\n').replace('\r', '\\r')
                    # 如果提供了来源标签，则在时间戳后添加
                    if source:
                        f.write(f"[{timestamp}] [{source}] {content_one_line}\n")
                    else:
                        f.write(f"[{timestamp}] {content_one_line}\n")
                    f.flush()
        except Exception as e:
            logger.exception(f"ForumEngine: 写入forum.log失败: {e}")
    
    def get_log_level(self, line: str) -> Optional[str]:
        """检测日志行的级别（INFO/ERROR/WARNING/DEBUG等）
        
        支持loguru格式：YYYY-MM-DD HH:mm:ss.SSS | LEVEL | ...
        
        Returns:
            'INFO', 'ERROR', 'WARNING', 'DEBUG' 或 None（无法识别）
        """
        # 检查loguru格式：YYYY-MM-DD HH:mm:ss.SSS | LEVEL | ...
        # 匹配模式：| LEVEL | 或 | LEVEL     |
        match = re.search(r'\|\s*(INFO|ERROR|WARNING|DEBUG|TRACE|CRITICAL)\s*\|', line)
        if match:
            return match.group(1)
        return None
    
    def is_target_log_line(self, line: str) -> bool:
        """检查是否是目标日志行（SummaryNode）
        
        支持多种识别方式：
        1. 类名：FirstSummaryNode, ReflectionSummaryNode
        2. 完整模块路径：InsightEngine.nodes.summary_node、MediaEngine.nodes.summary_node、QueryEngine.nodes.summary_node
        3. 部分模块路径：nodes.summary_node（兼容性）
        4. 关键标识文本：正在生成首次段落总结、正在生成反思总结
        
        排除条件：
        - ERROR 级别的日志（错误日志不应被识别为目标节点）
        - 包含错误关键词的日志（JSON解析失败、JSON修复失败等）
        """
        # 排除 ERROR 级别的日志
        log_level = self.get_log_level(line)
        if log_level == 'ERROR':
            return False
        
        # 兼容旧检查方式
        if "| ERROR" in line or "| ERROR    |" in line:
            return False
        
        # 排除包含错误关键词的日志
        error_keywords = ["JSON解析失败", "JSON修复失败", "Traceback", "File \""]
        for keyword in error_keywords:
            if keyword in line:
                return False
        
        # 检查是否包含目标节点模式
        for pattern in self.target_node_patterns:
            if pattern in line:
                return True
        return False
    
    def is_valuable_content(self, line: str) -> bool:
        """判断是否是有价值的内容（排除短小的提示信息和错误信息）"""
        # 如果包含"清理后的输出"，则认为是有价值的
        if "清理后的输出" in line:
            return True
        
        # 排除常见的短小提示信息和错误信息
        exclude_patterns = [
            "JSON解析失败",
            "JSON修复失败",
            "直接使用清理后的文本",
            "JSON解析成功",
            "成功生成",
            "已更新段落",
            "正在生成",
            "开始处理",
            "处理完成",
            "已读取HOST发言",
            "读取HOST发言失败",
            "未找到HOST发言",
            "调试输出",
            "信息记录"
        ]
        
        for pattern in exclude_patterns:
            if pattern in line:
                return False
        
        # 如果行长度过短，也认为不是有价值的内容
        # 移除时间戳：支持旧格式和新格式
        clean_line = re.sub(r'\[\d{2}:\d{2}:\d{2}\]', '', line)
        clean_line = re.sub(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3}\s*\|\s*[A-Z]+\s*\|\s*[^|]+?\s*-\s*', '', clean_line)
        clean_line = clean_line.strip()
        if len(clean_line) < 30:  # 阈值可以调整
            return False
            
        return True
    
    def is_json_start_line(self, line: str) -> bool:
        """判断是否是JSON开始行"""
        return "清理后的输出: {" in line
    
    def is_json_end_line(self, line: str) -> bool:
        """判断是否是JSON结束行
        
        只判断纯粹的结束标记行，不包含任何日志格式信息（时间戳等）。
        如果行包含时间戳，应该先清理再判断，但这里返回False表示需要进一步处理。
        """
        stripped = line.strip()
        
        # 如果行包含时间戳（旧格式或新格式），说明不是纯粹的结束行
        # 旧格式：[HH:MM:SS]
        if re.match(r'^\[\d{2}:\d{2}:\d{2}\]', stripped):
            return False
        # 新格式：YYYY-MM-DD HH:mm:ss.SSS
        if re.match(r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3}', stripped):
            return False
        
        # 不包含时间戳的行，检查是否是纯结束标记
        if stripped == "}" or stripped == "] }":
            return True
        return False
    
    def extract_json_content(self, json_lines: List[str]) -> Optional[str]:
        """从多行中提取并解析JSON内容"""
        try:
            # 找到JSON开始的位置
            json_start_idx = -1
            for i, line in enumerate(json_lines):
                if "清理后的输出: {" in line:
                    json_start_idx = i
                    break
            
            if json_start_idx == -1:
                return None
            
            # 提取JSON部分
            first_line = json_lines[json_start_idx]
            json_start_pos = first_line.find("清理后的输出: {")
            if json_start_pos == -1:
                return None
            
            json_part = first_line[json_start_pos + len("清理后的输出: "):]
            
            # 如果第一行就包含完整JSON，直接处理
            if json_part.strip().endswith("}") and json_part.count("{") == json_part.count("}"):
                try:
                    json_obj = json.loads(json_part.strip())
                    return self.format_json_content(json_obj)
                except json.JSONDecodeError:
                    # 单行JSON解析失败，尝试修复
                    fixed_json = self.fix_json_string(json_part.strip())
                    if fixed_json:
                        try:
                            json_obj = json.loads(fixed_json)
                            return self.format_json_content(json_obj)
                        except json.JSONDecodeError:
                            pass
                    return None
            
            # 处理多行JSON
            json_text = json_part
            for line in json_lines[json_start_idx + 1:]:
                # 移除时间戳：支持旧格式 [HH:MM:SS] 和新格式 loguru (YYYY-MM-DD HH:mm:ss.SSS | LEVEL | ...)
                # 旧格式：[HH:MM:SS]
                clean_line = re.sub(r'^\[\d{2}:\d{2}:\d{2}\]\s*', '', line)
                # 新格式：移除 loguru 格式的时间戳和级别信息
                # 格式: YYYY-MM-DD HH:mm:ss.SSS | LEVEL | module:function:line -
                clean_line = re.sub(r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3}\s*\|\s*[A-Z]+\s*\|\s*[^|]+?\s*-\s*', '', clean_line)
                json_text += clean_line
            
            # 尝试解析JSON
            try:
                json_obj = json.loads(json_text.strip())
                return self.format_json_content(json_obj)
            except json.JSONDecodeError:
                # 多行JSON解析失败，尝试修复
                fixed_json = self.fix_json_string(json_text.strip())
                if fixed_json:
                    try:
                        json_obj = json.loads(fixed_json)
                        return self.format_json_content(json_obj)
                    except json.JSONDecodeError:
                        pass
                return None
            
        except Exception as e:
            # 其他异常也不打印错误信息，直接返回None
            return None
    
    def format_json_content(self, json_obj: dict) -> str:
        """格式化JSON内容为可读形式"""
        try:
            # 提取主要内容，优先选择反思总结，其次是首次总结
            content = None
            
            if "updated_paragraph_latest_state" in json_obj:
                content = json_obj["updated_paragraph_latest_state"]
            elif "paragraph_latest_state" in json_obj:
                content = json_obj["paragraph_latest_state"]
            
            # 如果找到了内容，直接返回（保持换行符为\n）
            if content:
                return content
            
            # 如果没有找到预期的字段，返回整个JSON的字符串表示
            return f"清理后的输出: {json.dumps(json_obj, ensure_ascii=False, indent=2)}"
            
        except Exception as e:
            logger.exception(f"ForumEngine: 格式化JSON时出错: {e}")
            return f"清理后的输出: {json.dumps(json_obj, ensure_ascii=False, indent=2)}"

    def extract_node_content(self, line: str) -> Optional[str]:
        """提取节点内容，去除时间戳、节点名称等前缀"""
        content = line
        
        # 移除时间戳部分：支持旧格式和新格式
        # 旧格式: [HH:MM:SS]
        match_old = re.search(r'\[\d{2}:\d{2}:\d{2}\]\s*(.+)', content)
        if match_old:
            content = match_old.group(1).strip()
        else:
            # 新格式: YYYY-MM-DD HH:mm:ss.SSS | LEVEL | module:function:line -
            match_new = re.search(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3}\s*\|\s*[A-Z]+\s*\|\s*[^|]+?\s*-\s*(.+)', content)
            if match_new:
                content = match_new.group(1).strip()
        
        if not content:
            return line.strip()
        
        # 移除所有的方括号标签（包括节点名称和应用名称）
        content = re.sub(r'^\[.*?\]\s*', '', content)
        
        # 继续移除可能的多个连续标签
        while re.match(r'^\[.*?\]\s*', content):
            content = re.sub(r'^\[.*?\]\s*', '', content)
        
        # 移除常见前缀（如"首次总结: "、"反思总结: "等）
        prefixes_to_remove = [
            "首次总结: ",
            "反思总结: ",
            "清理后的输出: "
        ]
        
        for prefix in prefixes_to_remove:
            if content.startswith(prefix):
                content = content[len(prefix):]
                break
        
        # 移除可能存在的应用名标签（不在方括号内的）
        app_names = ['INSIGHT', 'MEDIA', 'QUERY']
        for app_name in app_names:
            # 移除单独的APP_NAME（在行首）
            content = re.sub(rf'^{app_name}\s+', '', content, flags=re.IGNORECASE)
        
        # 清理多余的空格
        content = re.sub(r'\s+', ' ', content)
        
        return content.strip()
   
    def get_file_size(self, file_path: Path) -> int:
        """获取文件大小"""
        try:
            return file_path.stat().st_size if file_path.exists() else 0
        except:
            return 0
   
    def get_file_line_count(self, file_path: Path) -> int:
        """获取文件行数"""
        try:
            if not file_path.exists():
                return 0
            with open(file_path, 'r', encoding='utf-8') as f:
                return sum(1 for _ in f)
        except:
            return 0
   
    def read_new_lines(self, file_path: Path, app_name: str) -> List[str]:
        """读取文件中的新行"""
        new_lines = []
       
        try:
            if not file_path.exists():
                return new_lines
           
            current_size = self.get_file_size(file_path)
            last_position = self.file_positions.get(app_name, 0)
           
            # 如果文件变小了，说明被清空了，重新从头开始
            if current_size < last_position:
                last_position = 0
                # 重置JSON捕获状态
                self.capturing_json[app_name] = False
                self.json_buffer[app_name] = []
                self.in_error_block[app_name] = False
           
            if current_size > last_position:
                with open(file_path, 'r', encoding='utf-8') as f:
                    f.seek(last_position)
                    new_content = f.read()
                    new_lines = new_content.split('\n')
                   
                    # 更新位置
                    self.file_positions[app_name] = f.tell()
                   
                    # 过滤空行
                    new_lines = [line.strip() for line in new_lines if line.strip()]
                   
        except Exception as e:
            logger.exception(f"ForumEngine: 读取{app_name}日志失败: {e}")
       
        return new_lines
   
    def process_lines_for_json(self, lines: List[str], app_name: str) -> List[str]:
        """处理行以捕获多行JSON内容
        
        实现ERROR块过滤：如果遇到ERROR级别的日志，拒绝处理直到遇到下一个INFO级别的日志
        """
        captured_contents = []
        
        # 初始化状态
        if app_name not in self.capturing_json:
            self.capturing_json[app_name] = False
            self.json_buffer[app_name] = []
        if app_name not in self.in_error_block:
            self.in_error_block[app_name] = False
        
        for line in lines:
            if not line.strip():
                continue
            
            # 首先检查日志级别，更新ERROR块状态
            log_level = self.get_log_level(line)
            if log_level == 'ERROR':
                # 遇到ERROR，进入ERROR块状态
                self.in_error_block[app_name] = True
                # 如果正在捕获JSON，立即停止并清空缓冲区
                if self.capturing_json[app_name]:
                    self.capturing_json[app_name] = False
                    self.json_buffer[app_name] = []
                # 跳过当前行，不处理
                continue
            elif log_level == 'INFO':
                # 遇到INFO，退出ERROR块状态
                self.in_error_block[app_name] = False
            # 其他级别（WARNING、DEBUG等）保持当前状态
            
            # 如果在ERROR块中，拒绝处理所有内容
            if self.in_error_block[app_name]:
                # 如果正在捕获JSON，立即停止并清空缓冲区
                if self.capturing_json[app_name]:
                    self.capturing_json[app_name] = False
                    self.json_buffer[app_name] = []
                # 跳过当前行，不处理
                continue
                
            # 检查是否是目标节点行和JSON开始标记
            is_target = self.is_target_log_line(line)
            is_json_start = self.is_json_start_line(line)
            
            # 只有目标节点（SummaryNode）的JSON输出才应该被捕获
            # 过滤掉SearchNode等其他节点的输出（它们不是目标节点，即使有JSON也不会被捕获）
            if is_target and is_json_start:
                # 开始捕获JSON（必须是目标节点且包含"清理后的输出: {"）
                self.capturing_json[app_name] = True
                self.json_buffer[app_name] = [line]
                self.json_start_line[app_name] = line
                
                # 检查是否是单行JSON
                if line.strip().endswith("}"):
                    # 单行JSON，立即处理
                    content = self.extract_json_content([line])
                    if content:  # 只有成功解析的内容才会被记录
                        # 去除重复的标签和格式化
                        clean_content = self._clean_content_tags(content, app_name)
                        captured_contents.append(f"{clean_content}")
                    self.capturing_json[app_name] = False
                    self.json_buffer[app_name] = []
                    
            elif is_target and self.is_valuable_content(line):
                # 其他有价值的SummaryNode内容（必须是目标节点且有价值）
                clean_content = self._clean_content_tags(self.extract_node_content(line), app_name)
                captured_contents.append(f"{clean_content}")
                    
            elif self.capturing_json[app_name]:
                # 正在捕获JSON的后续行
                self.json_buffer[app_name].append(line)
                
                # 检查是否是JSON结束
                # 先清理时间戳，然后判断清理后的行是否是结束标记
                cleaned_line = line.strip()
                # 清理旧格式时间戳：[HH:MM:SS]
                cleaned_line = re.sub(r'^\[\d{2}:\d{2}:\d{2}\]\s*', '', cleaned_line)
                # 清理新格式时间戳：YYYY-MM-DD HH:mm:ss.SSS | LEVEL | module:function:line -
                cleaned_line = re.sub(r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3}\s*\|\s*[A-Z]+\s*\|\s*[^|]+?\s*-\s*', '', cleaned_line)
                cleaned_line = cleaned_line.strip()
                
                # 清理后判断是否是结束标记
                if cleaned_line == "}" or cleaned_line == "] }":
                    # JSON结束，处理完整的JSON
                    content = self.extract_json_content(self.json_buffer[app_name])
                    if content:  # 只有成功解析的内容才会被记录
                        # 去除重复的标签和格式化
                        clean_content = self._clean_content_tags(content, app_name)
                        captured_contents.append(f"{clean_content}")
                    
                    # 重置状态
                    self.capturing_json[app_name] = False
                    self.json_buffer[app_name] = []
        
        return captured_contents
    
    def _trigger_host_speech(self, force: bool = False):
        """触发主持人发言（同步执行）"""
        if not HOST_AVAILABLE or self.is_host_generating:
            return
        
        try:
            # 设置生成标志
            self.is_host_generating = True
            
            required_count = 1 if force else min(max(self.host_speech_threshold, 1), 5)
            if len(self.agent_speeches_buffer) < required_count:
                self.is_host_generating = False
                return
            recent_batch_size = min(len(self.agent_speeches_buffer), 5)
            recent_speeches = self.agent_speeches_buffer[:recent_batch_size]
            
            logger.info("ForumEngine: 正在生成主持人发言...")
            
            # 调用主持人生成发言（传入最近5条）
            host_speech = generate_host_speech(recent_speeches)
            
            if host_speech:
                # 写入主持人发言到forum.log
                self.write_to_forum_log(host_speech, "HOST")
                logger.info(f"ForumEngine: 主持人发言已记录")
                self._host_trigger_count += 1
                self._emit("forum_host_speech",
                           node_name="ForumHost",
                           detail={"trigger_count": self._host_trigger_count,
                                   "speech_preview": host_speech[:80]})

                # 清空已处理的发言批次（最多5条）
                self.agent_speeches_buffer = self.agent_speeches_buffer[recent_batch_size:]
            else:
                logger.error("ForumEngine: 主持人发言生成失败")
            
            # 重置生成标志
            self.is_host_generating = False
                
        except Exception as e:
            logger.exception(f"ForumEngine: 触发主持人发言时出错: {e}")
            self.is_host_generating = False
    
    def _clean_content_tags(self, content: str, app_name: str) -> str:
        """清理内容中的重复标签和多余前缀"""
        if not content:
            return content
            
        # 先去除所有可能的标签格式（包括 [INSIGHT]、[MEDIA]、[QUERY] 等）
        # 使用更强力的清理方式
        all_app_names = ['INSIGHT', 'MEDIA', 'QUERY']
        
        for name in all_app_names:
            # 去除 [APP_NAME] 格式（大小写不敏感）
            content = re.sub(rf'\[{name}\]\s*', '', content, flags=re.IGNORECASE)
            # 去除单独的 APP_NAME 格式
            content = re.sub(rf'^{name}\s+', '', content, flags=re.IGNORECASE)
        
        # 去除任何其他的方括号标签
        content = re.sub(r'^\[.*?\]\s*', '', content)
        
        # 去除可能的重复空格
        content = re.sub(r'\s+', ' ', content)
        
        return content.strip()
   
    def monitor_logs(self):
        """智能监控日志文件"""
        logger.info("ForumEngine: 论坛创建中...")
       
        # 初始化文件行数和位置 - 记录当前状态作为基线
        for app_name, log_file in self.monitored_logs.items():
            self.file_line_counts[app_name] = self.get_file_line_count(log_file)
            self.file_positions[app_name] = self.get_file_size(log_file)
            self.capturing_json[app_name] = False
            self.json_buffer[app_name] = []
            self.in_error_block[app_name] = False
            # logger.info(f"ForumEngine: {app_name} 基线行数: {self.file_line_counts[app_name]}")
       
        while self.is_monitoring:
            try:
                # 同时检测三个log文件的变化
                any_growth = False
                any_shrink = False
                captured_any = False
               
                # 为每个log文件独立处理
                for app_name, log_file in self.monitored_logs.items():
                    current_lines = self.get_file_line_count(log_file)
                    previous_lines = self.file_line_counts.get(app_name, 0)
                   
                    if current_lines > previous_lines:
                        any_growth = True
                        # 立即读取新增内容
                        new_lines = self.read_new_lines(log_file, app_name)
                       
                        # 先检查是否需要触发搜索（只触发一次）
                        if not self.is_searching:
                            for line in new_lines:
                                # 检查是否包含目标节点模式（支持多种格式）
                                if line.strip() and self.is_target_log_line(line):
                                    # 进一步确认是首次总结节点（FirstSummaryNode或包含"正在生成首次段落总结"）
                                    if 'FirstSummaryNode' in line or '正在生成首次段落总结' in line:
                                        logger.info(f"ForumEngine: 在{app_name}中检测到第一次论坛发表内容")
                                        self.is_searching = True
                                        self.search_inactive_count = 0
                                        self._forum_speech_count = 0
                                        self._host_trigger_count = 0
                                        self._emit("forum_started",
                                                   detail={"trigger_app": app_name})
                                        # 清空forum.log开始新会话
                                        self.clear_forum_log()
                                        break  # 找到一个就够了，跳出循环
                       
                        # 处理所有新增内容（如果正在搜索状态）
                        if self.is_searching:
                            # 使用新的处理逻辑
                            captured_contents = self.process_lines_for_json(new_lines, app_name)
                            
                            for content in captured_contents:
                                # 将app_name转换为大写作为标签（如 insight -> INSIGHT）
                                source_tag = app_name.upper()
                                self.write_to_forum_log(content, source_tag)
                                captured_any = True
                                self._forum_speech_count += 1
                                self._emit("forum_speech",
                                           node_name=source_tag,
                                           detail={"speech_idx": self._forum_speech_count,
                                                   "content_preview": content[:80]})

                                # 将发言添加到缓冲区（格式化为完整的日志行）
                                timestamp = datetime.now().strftime('%H:%M:%S')
                                log_line = f"[{timestamp}] [{source_tag}] {content}"
                                self.agent_speeches_buffer.append(log_line)

                                # 检查是否需要触发主持人发言
                                if len(self.agent_speeches_buffer) >= self.host_speech_threshold and not self.is_host_generating:
                                    # 同步触发主持人发言
                                    self._trigger_host_speech()
                   
                    elif current_lines < previous_lines:
                        any_shrink = True
                        # logger.info(f"ForumEngine: 检测到 {app_name} 日志缩短，将重置基线")
                        # 重置文件位置到新的文件末尾
                        self.file_positions[app_name] = self.get_file_size(log_file)
                        # 重置JSON捕获状态
                        self.capturing_json[app_name] = False
                        self.json_buffer[app_name] = []
                        self.in_error_block[app_name] = False
                   
                    # 更新行数记录
                    self.file_line_counts[app_name] = current_lines
               
                # 检查是否应该结束当前搜索会话
                if self.is_searching:
                    if any_shrink:
                        self.is_searching = False
                        self.search_inactive_count = 0
                        self.agent_speeches_buffer = []
                        self.is_host_generating = False
                        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        self.write_to_forum_log(f"=== ForumEngine 论坛结束 - {end_time} ===", "SYSTEM")
                        self._emit("forum_ended",
                                   detail={"reason": "log_shrunk",
                                           "speech_count": self._forum_speech_count,
                                           "host_triggers": self._host_trigger_count})
                    elif not any_growth and not captured_any:
                        self.search_inactive_count += 1
                        if self.search_inactive_count >= 7200:  # 超时无活动自动结束
                            logger.info("ForumEngine: 长时间无活动，结束论坛")
                            self.is_searching = False
                            self.search_inactive_count = 0
                            self.agent_speeches_buffer = []
                            self.is_host_generating = False
                            end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            self.write_to_forum_log(f"=== ForumEngine 论坛结束 - {end_time} ===", "SYSTEM")
                            self._emit("forum_ended",
                                       detail={"reason": "timeout",
                                               "speech_count": self._forum_speech_count,
                                               "host_triggers": self._host_trigger_count})
                    else:
                        self.search_inactive_count = 0  # 重置计数器
               
                # 短暂休眠
                time.sleep(1)
               
            except Exception as e:
                logger.exception(f"ForumEngine: 论坛记录中出错: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(2)
       
        logger.info("ForumEngine: 停止论坛日志文件")
   
    def start_monitoring(self):
        """开始智能监控"""
        if self.is_monitoring:
            logger.info("ForumEngine: 论坛已经在运行中")
            return False
       
        try:
            # 启动监控
            self.is_monitoring = True
            self.monitor_thread = threading.Thread(target=self.monitor_logs, daemon=True)
            self.monitor_thread.start()
           
            logger.info("ForumEngine: 论坛已启动")
            return True
           
        except Exception as e:
            logger.exception(f"ForumEngine: 启动论坛失败: {e}")
            self.is_monitoring = False
            return False
   
    def stop_monitoring(self):
        """停止监控"""
        if not self.is_monitoring:
            logger.info("ForumEngine: 论坛未运行")
            return
       
        try:
            self.is_monitoring = False
           
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=2)
           
            # 写入结束标记
            end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.write_to_forum_log(f"=== ForumEngine 论坛结束 - {end_time} ===", "SYSTEM")
           
            logger.info("ForumEngine: 论坛已停止")
           
        except Exception as e:
            logger.exception(f"ForumEngine: 停止论坛失败: {e}")
   
    def get_forum_log_content(self) -> List[str]:
        """获取forum.log的内容"""
        try:
            if not self.forum_log_file.exists():
                return []
           
            with open(self.forum_log_file, 'r', encoding='utf-8') as f:
                return [line.rstrip('\n\r') for line in f.readlines()]
               
        except Exception as e:
            logger.exception(f"ForumEngine: 读取forum.log失败: {e}")
            return []

    def fix_json_string(self, json_text: str) -> str:
        """修复JSON字符串中的常见问题，特别是未转义的双引号"""
        try:
            # 尝试直接解析，如果成功则返回原文本
            json.loads(json_text)
            return json_text
        except json.JSONDecodeError:
            pass
        
        # 修复未转义的双引号问题
        # 这是一个更智能的修复方法，专门处理字符串值中的双引号
        
        try:
            # 使用状态机方法修复JSON
            # 遍历字符，跟踪是否在字符串值内部
            
            fixed_text = ""
            i = 0
            in_string = False
            escape_next = False
            
            while i < len(json_text):
                char = json_text[i]
                
                if escape_next:
                    # 处理转义字符
                    fixed_text += char
                    escape_next = False
                    i += 1
                    continue
                
                if char == '\\':
                    # 转义字符
                    fixed_text += char
                    escape_next = True
                    i += 1
                    continue
                
                if char == '"' and not escape_next:
                    # 遇到双引号
                    if in_string:
                        # 在字符串内部，检查下一个字符
                        # 如果下一个字符是冒号或者逗号或者大括号，说明这是字符串结束
                        next_char_pos = i + 1
                        while next_char_pos < len(json_text) and json_text[next_char_pos].isspace():
                            next_char_pos += 1
                        
                        if next_char_pos < len(json_text):
                            next_char = json_text[next_char_pos]
                            if next_char in [':', ',', '}']:
                                # 这是字符串结束，退出字符串状态
                                in_string = False
                                fixed_text += char
                            else:
                                # 这是字符串内部的引号，需要转义
                                fixed_text += '\\"'
                        else:
                            # 文件结束，退出字符串状态
                            in_string = False
                            fixed_text += char
                    else:
                        # 字符串开始
                        in_string = True
                        fixed_text += char
                else:
                    # 其他字符
                    fixed_text += char
                
                i += 1
            
            # 尝试解析修复后的JSON
            try:
                json.loads(fixed_text)
                return fixed_text
            except json.JSONDecodeError:
                # 修复失败，返回None
                return None
                
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Wave 4：事件驱动扩展
    # ------------------------------------------------------------------

    def bind_tasks(self, task_ids: List[str]) -> None:
        """
        绑定多个 task_id（对应三引擎各自的研究任务）。

        事件驱动模式下，ForumEngine 将监控这些 task_id 在
        task_events 表中的进度事件，而不再读取 .log 文件。

        同时保留 bind_task() 的单任务绑定以向后兼容。
        """
        self._tracked_task_ids: List[str] = list(task_ids)
        self._last_poll_time: Optional[str] = None
        self._event_paragraph_done_count: int = 0

        if task_ids:
            logger.info(
                f"ForumEngine: 已绑定 {len(task_ids)} 个 task_id（事件驱动模式）：{task_ids}"
            )

        # 同时绑定第一个作为主 task_id（兼容单任务 _emit 逻辑）
        if task_ids:
            self.bind_task(task_ids[0])

    def poll_events(
        self,
        task_ids: Optional[List[str]] = None,
        since: Optional[str] = None,
        limit: int = 100,
    ) -> List[dict]:
        """
        从 task_events 表查询指定任务的新结构化事件。

        Args:
            task_ids: 要查询的 task_id 列表；为 None 时使用 bind_tasks 绑定的列表
            since: ISO 时间字符串，只返回此时间之后的事件；为 None 时不过滤
            limit: 每个 task_id 最多返回多少事件

        Returns:
            按 created_at 升序排列的事件列表
        """
        if not _TASK_STORE_AVAILABLE or _get_task_store is None:
            return []

        ids = task_ids or getattr(self, "_tracked_task_ids", [])
        if not ids:
            return []

        try:
            store = _get_task_store()
            all_events: List[dict] = []
            for tid in ids:
                events = store.list_events(tid, limit=limit)
                all_events.extend(events)

            if since:
                all_events = [e for e in all_events if e.get("created_at", "") > since]

            all_events.sort(key=lambda e: e.get("created_at", ""))
            return all_events

        except Exception as exc:
            logger.warning(f"ForumEngine: poll_events 失败，忽略继续: {exc}")
            return []

    def _should_trigger_host_from_events(self, events: List[dict]) -> bool:
        """
        根据事件列表判断是否触发主持人发言。

        触发条件：累计接收到的 paragraph_done 事件数达到阈值。
        （替代旧的"每5条 .log 行"触发机制）
        """
        self._force_host_from_events = self._should_force_host_from_events(events)
        if self._force_host_from_events:
            return True

        paragraph_dones = [e for e in events if e.get("event_type") == "paragraph_done"]
        self._event_paragraph_done_count = getattr(self, "_event_paragraph_done_count", 0)
        self._event_paragraph_done_count += len(paragraph_dones)
        return self._event_paragraph_done_count >= self.host_speech_threshold

    @staticmethod
    def _should_force_host_from_events(events: List[dict]) -> bool:
        for evt in events:
            if evt.get("event_type") != "paragraph_done":
                continue
            detail = evt.get("detail") or {}
            gap_types = {str(item).lower() for item in (detail.get("gap_types") or [])}
            evidence_conflicts = int(detail.get("evidence_conflict_count") or 0)
            if "conflict" in gap_types or evidence_conflicts > 0:
                return True
        return False

    def _process_events_for_speeches(self, events: List[dict]) -> List[str]:
        """
        将结构化事件转换为 agent 发言文本，用于主持人触发。

        提取 paragraph_done 事件中的摘要信息写入论坛日志。
        """
        speeches: List[str] = []
        for evt in events:
            if evt.get("event_type") != "paragraph_done":
                continue
            detail = evt.get("detail") or {}
            node_name = evt.get("node_name") or "Agent"
            progress = detail.get("progress_pct", "")
            summary_parts = [f"段落研究完成 ({progress}%)" if progress else "段落研究完成"]
            gap_types = [str(item) for item in (detail.get("gap_types") or []) if str(item).strip()]
            if gap_types:
                summary_parts.append(f"gap={','.join(gap_types)}")
            evidence_conflicts = int(detail.get("evidence_conflict_count") or 0)
            if evidence_conflicts > 0:
                summary_parts.append(f"evidence_conflicts={evidence_conflicts}")
            if detail.get("conservative_expression_applied"):
                summary_parts.append("保守表达已启用")
            summary_hint = "；".join(summary_parts)

            speech_text = f"[{node_name}] {summary_hint}"
            speeches.append(speech_text)

            # 写入 forum.log 兼容层（保持 Socket.IO → 前端推送正常工作）
            source_label = (
                str(detail.get("engine", "")).strip()
                or str(evt.get("task_id", ""))[:6]
                or "AGENT"
            )
            self.write_to_forum_log(summary_hint, source_label.upper())

            self._forum_speech_count += 1
            self._emit(
                "forum_speech",
                detail={
                    "task_id": evt.get("task_id"),
                    "event_source": "task_events",
                    "speech_count": self._forum_speech_count,
                },
            )

        return speeches

    def _event_driven_loop(self) -> None:
        """
        事件驱动监控主循环（替代旧的文件 tail 循环）。

        每隔 1 秒 poll 一次 task_events，解析 paragraph_done 事件，
        当累计事件数超过阈值时触发主持人发言。
        forum.log 写入保持兼容（Socket.IO 仍依赖它推送前端）。
        """
        poll_interval = 1.0  # 秒
        logger.info("ForumEngine: 进入事件驱动监控循环")

        while self.is_monitoring:
            try:
                events = self.poll_events(since=self._last_poll_time)

                if events:
                    # 更新 since 时间戳，下次只取新事件
                    self._last_poll_time = events[-1].get("created_at")

                    # 转换为 agent speeches，写 forum.log
                    speeches = self._process_events_for_speeches(events)
                    if speeches:
                        self.agent_speeches_buffer.extend(speeches)

                    # 判断是否触发主持人
                    if self._should_trigger_host_from_events(events):
                        self._event_paragraph_done_count = 0  # 重置计数器
                        force_host = bool(getattr(self, "_force_host_from_events", False))
                        host_thread = threading.Thread(
                            target=self._trigger_host_speech,
                            kwargs={"force": force_host},
                            daemon=True,
                        )
                        host_thread.start()

            except Exception as exc:
                logger.error(f"ForumEngine: 事件驱动循环异常：{exc}")

            time.sleep(poll_interval)

        logger.info("ForumEngine: 事件驱动监控循环已退出")

    def start_event_driven_monitoring(self) -> bool:
        """
        以事件驱动模式启动 ForumEngine 监控。
        需要先调用 bind_tasks() 绑定研究任务的 task_id。
        """
        if self.is_monitoring:
            logger.info("ForumEngine: 监控已在运行中")
            return True

        if not _TASK_STORE_AVAILABLE:
            logger.warning("ForumEngine: task_store 不可用，事件驱动模式降级到文件监听")
            return self.start_monitoring()

        self.is_monitoring = True
        self._last_poll_time = None
        self._event_paragraph_done_count = 0

        self.monitor_thread = threading.Thread(
            target=self._event_driven_loop, daemon=True,
            name="forum-event-driven-monitor",
        )
        self.monitor_thread.start()
        logger.info("ForumEngine: 事件驱动监控已启动")
        return True


# 全局监控器实例
_monitor_instance = None

def get_monitor() -> LogMonitor:
    """获取全局监控器实例"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = LogMonitor()
    return _monitor_instance

def start_forum_monitoring():
    """启动ForumEngine智能监控"""
    return get_monitor().start_monitoring()

def stop_forum_monitoring():
    """停止ForumEngine监控"""
    get_monitor().stop_monitoring()

def get_forum_log():
    """获取forum.log内容"""
    return get_monitor().get_forum_log_content()
