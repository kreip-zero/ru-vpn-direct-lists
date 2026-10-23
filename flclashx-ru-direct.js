// FlClashX / Mihomo override-скрипт с автообновляемым списком.
// Весь трафик идёт через VPN (как в подписке). Напрямую уходят только домены из списка в твоём
// GitHub-репозитории: его пересобирает GitHub Actions каждые 6 часов, а клиент подтягивает файл сам.

const main = (config) => {
  // === НАСТРОЙКИ ===
  const GITHUB_USER = "kreip-zero";
  const REPO = "ru-vpn-direct-lists";
  const LIST = "full"; // "full" = шире (UnRKN + strict), "strict" = только сайты, закрытые для зарубежных IP

  // Сайты, которые нужно пустить напрямую прямо сейчас, не дожидаясь обновления списка.
  // Обычно проще дописать домен в custom.txt в репозитории.
  const extraDirect = [
    // "example.ru",
  ];

  config["mode"] = "rule";

  const groups = config["proxy-groups"] || [];
  const vpnGroup = (groups.find((g) => g.type === "select") || groups[0] || {}).name;

  // Список скачивается через VPN-группу, чтобы не зависеть от доступности GitHub в твоей сети
  const provider = {
    type: "http",
    behavior: "domain",
    format: "text",
    url: `https://raw.githubusercontent.com/${GITHUB_USER}/${REPO}/main/ru-direct-${LIST}.txt`,
    path: "./ru-direct.txt",
    interval: 21600,
  };
  if (vpnGroup) provider.proxy = vpnGroup;

  config["rule-providers"] = { ...(config["rule-providers"] || {}), "ru-direct": provider };

  const myRules = [
    "IP-CIDR,127.0.0.0/8,DIRECT,no-resolve",
    "IP-CIDR,192.168.0.0/16,DIRECT,no-resolve",
    "IP-CIDR,10.0.0.0/8,DIRECT,no-resolve",
    "IP-CIDR,172.16.0.0/12,DIRECT,no-resolve",
    ...extraDirect.map((d) => `DOMAIN-SUFFIX,${d},DIRECT`),
    "RULE-SET,ru-direct,DIRECT",
  ];

  if (Array.isArray(config.rules) && config.rules.length > 0) {
    // Наши правила в начале: приоритетнее правил подписки. Остальное решает подписка (VPN).
    config.rules.unshift(...myRules);
  } else {
    config.rules = [...myRules, `MATCH,${vpnGroup || "PROXY"}`];
  }

  return config;
};
