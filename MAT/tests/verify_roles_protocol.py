import asyncio
from MAT.roles.research_analyst import ResearchAnalyst
from MAT.roles.technical_analyst import TechnicalAnalyst
from MAT.roles.sentiment_analyst import SentimentAnalyst
from MAT.roles.alpha_strategist import AlphaStrategist
from MAT.schemas import FAReport, TAReport, SAReport

async def check_roles():
    print("🔍 启动角色协议完整性审计...")
    
    # 1. 检测 RA 是否清理了旧指标
    ra = ResearchAnalyst()
    print(f"✅ RA 初始化成功")
    
    # 2. 检测 AS 是否订阅了正确的报告类型
    as_agent = AlphaStrategist()
    watched_actions = as_agent.watched_actions
    expected_reports = {"PublishFAReport", "PublishTAReport", "PublishSAReport", "PublishInvestigationReport"}
    # 检查 AS 观察的动作名
    actual_actions = {a.__name__ if hasattr(a, '__name__') else str(a) for a in watched_actions}
    print(f"📡 AS 正在监听: {actual_actions}")
    
    if expected_reports.issubset(actual_actions):
        print("✅ AS 订阅协议达标")
    else:
        print(f"❌ AS 订阅缺失: {expected_reports - actual_actions}")

    # 3. 检查 AS 是否持有缓存字典
    if hasattr(as_agent, '_ticker_states') or hasattr(as_agent, 'buffer'):
        print("✅ AS 报告缓冲机制已就绪")
    else:
        print("⚠️ 未发现 AS 显式缓冲字典，请确认其如何处理异步消息收集")

if __name__ == "__main__":
    asyncio.run(check_roles())