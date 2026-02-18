"""
应用常量配置
"""

# 邮件内容长度限制
MAX_SUBJECT_LENGTH = 255
MAX_FROM_ADDRESS_LENGTH = 255
MAX_TO_ADDRESSES_LENGTH = 1000
MAX_BODY_TEXT_LENGTH = 5000
MAX_BODY_HTML_LENGTH = 10000
MAX_FROM_NAME_LENGTH = 100

# IMAP 配置
IMAP_DEFAULT_PORT = 993
IMAP_CONNECTION_TIMEOUT = 30
IMAP_FETCH_LIMIT_DEFAULT = 50

# 文件夹配置
FOLDER_CONFIGS = {
    "gmail": [
        ("INBOX", "收件箱", "inbox"),
        ("[Gmail]/&V4NXPpCuTvY-", "垃圾邮件", "spam"),  # Gmail 垃圾箱（UTF-7编码）
    ],
    "default": [
        ("INBOX", "收件箱", "inbox"),
        ("Junk", "垃圾邮件", "spam"),
    ],
    "microsoft": [
        ("Inbox", "收件箱", "inbox"),
        ("JunkEmail", "垃圾邮件", "spam"),
    ]
}

# OAuth2 配置
MICROSOFT_TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GRAPH_URL = "https://graph.microsoft.com/v1.0"

# 批量操作配置
BATCH_CHECK_EXISTING_EMAILS = 100  # 批量检查邮件是否存在的数量
