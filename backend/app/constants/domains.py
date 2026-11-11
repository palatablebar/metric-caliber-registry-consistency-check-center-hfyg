"""Business domains of the 微光课堂 metric registry."""
from enum import Enum


class Domain(str, Enum):
    GROWTH = "growth"
    TRADE = "trade"
    CONTENT = "content"
    EXPERIENCE = "experience"


ALL_DOMAINS = [d.value for d in Domain]
DOMAIN_LABELS = {
    Domain.GROWTH.value: "增长",
    Domain.TRADE.value: "交易",
    Domain.CONTENT.value: "内容",
    Domain.EXPERIENCE.value: "体验",
}
DOMAIN_ORDER = ALL_DOMAINS
