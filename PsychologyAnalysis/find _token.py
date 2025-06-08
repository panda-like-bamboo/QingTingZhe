import dashscope
from dashscope import Account

# 配置您的API Key
dashscope.api_key = 'sk-0ffc64dd9d614c0088ee28e3a072420a'

# 查询账户信息
account = Account()
balance = account.get_balance()
print(balance)