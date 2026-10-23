#!/usr/bin/env python3
"""Собирает списки доменов, которые надо пускать в обход VPN (DIRECT) в Clash/Mihomo.

Источники скачиваются заново при каждом запуске. Если источник недоступен или вернул
подозрительно мало данных, берётся его последняя удачная копия из sources/.

Результат:
  ru-direct-strict.txt  - домены, которые пускают только с российских IP
                          (ru-available-only-inside) + curated-список hydraponique + custom.txt
  ru-direct-full.txt    - strict + список UnRKN (сервисы, которые режут или палят VPN)
  Оба файла в формате Mihomo rule-provider (behavior=domain, format=text).

  geosite/ru-direct.dat        - те же списки как geosite.dat (теги RU-DIRECT-STRICT, RU-DIRECT-FULL)
  clients/happ, clients/incy   - профили маршрутизации (JSON) и диплинки для Happ и Incy
  sing-box/ru-direct-*.json    - rule-set в формате source для клиентов на sing-box
"""
import datetime
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "sources")

UNRKN_URL = "https://raw.githubusercontent.com/UnRKN/ru-blocklist/main/ru-blocklist-ext.txt"
HYDRA_URL = "https://raw.githubusercontent.com/hydraponique/roscomvpn-geosite/master/data/category-ru"
GEOSITE_URL = "https://github.com/runetfreedom/russia-v2ray-rules-dat/releases/latest/download/geosite.dat"
GEOSITE_TAG = "ru-available-only-inside"

MIN_LINES = {"unrkn": 300, "inside": 80, "hydra": 20}
DOMAIN_RE = re.compile(r"^[a-z0-9_-]+(\.[a-z0-9_-]+)+$")


def download(url, timeout=300):
    req = urllib.request.Request(url, headers={"User-Agent": "ru-vpn-direct-lists"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def normalize(lines):
    out = set()
    for line in lines:
        line = line.split("#", 1)[0].strip().lower()
        if not line or "@" in line:
            continue
        for prefix in ("domain:", "full:"):
            if line.startswith(prefix):
                line = line[len(prefix):]
        line = line.lstrip(".").lstrip("*.").strip()
        if DOMAIN_RE.match(line):
            out.add(line)
    return out


# --- минимальный разбор geosite.dat (protobuf), без внешних зависимостей ---
def _varint(b, i):
    r = s = 0
    while True:
        c = b[i]
        i += 1
        r |= (c & 0x7F) << s
        s += 7
        if not c & 0x80:
            return r, i


def _fields(b):
    i = 0
    while i < len(b):
        k, i = _varint(b, i)
        f, w = k >> 3, k & 7
        if w == 0:
            v, i = _varint(b, i)
        elif w == 2:
            n, i = _varint(b, i)
            v = b[i:i + n]
            i += n
        elif w == 1:
            v = b[i:i + 8]
            i += 8
        elif w == 5:
            v = b[i:i + 4]
            i += 4
        else:
            raise ValueError("unsupported wire type")
        yield f, v


def geosite_domains(data, tag):
    for f, v in _fields(data):
        if f != 1:
            continue
        code, doms = None, []
        for f2, v2 in _fields(v):
            if f2 == 1:
                code = v2.decode()
            elif f2 == 2:
                doms.append(v2)
        if code and code.lower() == tag:
            res = []
            for d in doms:
                dtype, val = 0, ""
                for f3, v3 in _fields(d):
                    if f3 == 1:
                        dtype = v3
                    elif f3 == 2:
                        val = v3.decode()
                # 2 = domain (суффикс), 3 = full (точное совпадение); regex/keyword пропускаем
                if dtype in (2, 3):
                    res.append(val)
            return res
    return []


def fetch_source(name, getter):
    path = os.path.join(SRC, name + ".txt")
    try:
        domains = normalize(getter())
        if len(domains) < MIN_LINES[name]:
            raise ValueError(f"получено только {len(domains)} доменов")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(sorted(domains)) + "\n")
        print(f"[ok]   {name}: {len(domains)} доменов (обновлён)")
        return domains
    except Exception as e:  # noqa: BLE001
        print(f"[WARN] {name}: {e}; беру сохранённую копию", file=sys.stderr)
        with open(path, encoding="utf-8") as f:
            return normalize(f.read().splitlines())


def read_list(filename):
    path = os.path.join(ROOT, filename)
    if not os.path.exists(path):
        return set()
    with open(path, encoding="utf-8") as f:
        return normalize(f.read().splitlines())


def covered(domain, domains):
    parts = domain.split(".")
    return any(".".join(parts[i:]) in domains for i in range(1, len(parts) - 1))


def reduce(domains, exclude):
    # исключения: сам домен и всё, что под ним
    kept = {d for d in domains if d not in exclude and not covered(d, exclude)}
    # поддомен не нужен, если родитель уже в списке
    return sorted(d for d in kept if not covered(d, kept))


def write_list(filename, domains, title):
    stamp = datetime.date.today().isoformat()
    with open(os.path.join(ROOT, filename), "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# {title}\n# Формат Mihomo: behavior=domain, format=text. Всего: {len(domains)}\n")
        for d in domains:
            f.write(f"+.{d}\n")
    print(f"[out]  {filename}: {len(domains)} доменов ({stamp})")


# --- geosite.dat: свой файл с двумя тегами для Happ, Incy и любых клиентов на Xray ---
GEOSITE_TAGS = {"strict": "RU-DIRECT-STRICT", "full": "RU-DIRECT-FULL"}
GEOSITE_OUT = os.path.join("geosite", "ru-direct.dat")


def _enc_varint(n):
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def _enc_bytes(field, payload):
    return _enc_varint((field << 3) | 2) + _enc_varint(len(payload)) + payload


def build_geosite(lists):
    """lists: {тег: [домены]}. Тип 2 = domain (сам домен и все поддомены)."""
    out = b""
    for tag, domains in lists.items():
        site = _enc_bytes(1, tag.encode())
        for d in domains:
            dom = _enc_varint(1 << 3) + _enc_varint(2) + _enc_bytes(2, d.encode())
            site += _enc_bytes(2, dom)
        out += _enc_bytes(1, site)
    return out


def write_geosite(lists):
    data = build_geosite(lists)
    # проверка: файл читается обратно и совпадает с исходными списками
    for tag, domains in lists.items():
        if sorted(geosite_domains(data, tag.lower())) != sorted(domains):
            raise RuntimeError(f"geosite.dat: тег {tag} не совпал после чтения")
    path = os.path.join(ROOT, GEOSITE_OUT)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)
    print(f"[out]  {GEOSITE_OUT}: {len(data)} байт, теги {', '.join(lists)}")


# --- профили маршрутизации Happ и Incy (формат совпадает, различается схема диплинка) ---
CDN_BASE = "https://cdn.jsdelivr.net/gh/kreip-zero/ru-vpn-direct-lists@main"
PROFILE_UPDATED = "1792744158"  # менять вручную, когда меняется структура профиля
CLIENT_SCHEMES = {"happ": "happ", "incy": "incy"}


def profile(kind):
    return {
        "Name": f"RU Direct ({kind})",
        "GlobalProxy": "true",
        "UseChunkFiles": "false",
        "RemoteDns": "8.8.8.8",
        "DomesticDns": "77.88.8.8",
        "RemoteDNSType": "DoH",
        "RemoteDNSDomain": "https://8.8.8.8/dns-query",
        "RemoteDNSIP": "8.8.8.8",
        "DomesticDNSType": "DoH",
        "DomesticDNSDomain": "https://77.88.8.8/dns-query",
        "DomesticDNSIP": "77.88.8.8",
        "Geoipurl": "https://cdn.jsdelivr.net/gh/hydraponique/roscomvpn-geoip/release/geoip.dat",
        "Geositeurl": f"{CDN_BASE}/{GEOSITE_OUT.replace(os.sep, '/')}",
        "LastUpdated": PROFILE_UPDATED,
        "RouteOrder": "block-proxy-direct",
        "DirectSites": [f"geosite:{GEOSITE_TAGS[kind]}"],
        "DirectIp": [
            "10.0.0.0/8",
            "172.16.0.0/12",
            "192.168.0.0/16",
            "169.254.0.0/16",
            "224.0.0.0/4",
            "255.255.255.255",
        ],
        "ProxySites": [],
        "ProxyIp": [],
        "BlockSites": [],
        "BlockIp": [],
        "DomainStrategy": "IPIfNonMatch",
        "FakeDNS": "false",
    }


def write_profiles():
    import base64
    import json

    for client, scheme in CLIENT_SCHEMES.items():
        folder = os.path.join(ROOT, "clients", client)
        os.makedirs(folder, exist_ok=True)
        for kind in GEOSITE_TAGS:
            data = profile(kind)
            with open(os.path.join(folder, f"ru-direct-{kind}.json"), "w", encoding="utf-8", newline="\n") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.write("\n")
            compact = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode()
            link = f"{scheme}://routing/onadd/{base64.b64encode(compact).decode()}"
            with open(os.path.join(folder, f"ru-direct-{kind}.deeplink"), "w", encoding="utf-8", newline="\n") as f:
                f.write(link + "\n")
    print("[out]  clients/happ, clients/incy: профили и диплинки")


# --- sing-box: rule-set в виде исходного JSON (format: source) ---
def write_singbox(lists):
    import json

    folder = os.path.join(ROOT, "sing-box")
    os.makedirs(folder, exist_ok=True)
    for kind, domains in lists.items():
        data = {"version": 2, "rules": [{"domain_suffix": domains}]}
        with open(os.path.join(folder, f"ru-direct-{kind}.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
            f.write("\n")
    print("[out]  sing-box: ru-direct-strict.json, ru-direct-full.json")


def main():
    os.makedirs(SRC, exist_ok=True)
    unrkn = fetch_source("unrkn", lambda: download(UNRKN_URL).decode("utf-8").splitlines())
    hydra = fetch_source("hydra", lambda: download(HYDRA_URL).decode("utf-8").splitlines())
    inside = fetch_source(
        "inside", lambda: geosite_domains(download(GEOSITE_URL), GEOSITE_TAG)
    )
    custom = read_list("custom.txt")
    exclude = read_list("exclude.txt")

    strict = reduce(inside | hydra | custom, exclude)
    full = reduce(inside | hydra | custom | unrkn, exclude)

    write_list(
        "ru-direct-strict.txt",
        strict,
        "Сайты, доступные только с российских IP (geoblock) + custom.txt",
    )
    write_list(
        "ru-direct-full.txt",
        full,
        "strict + сервисы из UnRKN/ru-blocklist, которые режут или палят VPN",
    )

    write_geosite({GEOSITE_TAGS["strict"]: strict, GEOSITE_TAGS["full"]: full})
    write_profiles()
    write_singbox({"strict": strict, "full": full})

    # раз в неделю меняем этот файл, чтобы GitHub не отключил расписание из-за неактивности репозитория
    year, week, _ = datetime.date.today().isocalendar()
    with open(os.path.join(ROOT, "updated.txt"), "w", encoding="utf-8") as f:
        f.write(f"{year}-W{week:02d}\n")


if __name__ == "__main__":
    main()
