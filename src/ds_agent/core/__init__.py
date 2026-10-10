# core 包：审批与附件。
from ds_agent.core.approval import ApprovalManager, ApprovalResult
from ds_agent.core.attachments import attach_file, attach_folder, attach_path

__all__ = [
    "ApprovalManager",
    "ApprovalResult",
    "attach_file",
    "attach_folder",
    "attach_path",
]
