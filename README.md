# ru-vpn-direct-lists

[![Update lists](https://github.com/kreip-zero/ru-vpn-direct-lists/actions/workflows/update.yml/badge.svg)](https://github.com/kreip-zero/ru-vpn-direct-lists/actions/workflows/update.yml)

**Российские сайты, которые не открываются через VPN: готовый список для FlClashX, Happ, Incy, Hiddify и других клиентов. Обновляется сам.**

*English: a self-updating domain list of Russian websites that block VPN and foreign IPs. Ready-made configs for Mihomo (Clash Meta), Happ, Incy, sing-box and Xray clients: these domains go `DIRECT`, everything else stays on your VPN.*

## Зачем это нужно

Ты в России, VPN включён. Зарубежные сайты работают, а российские нет: Госуслуги, банки, маркетплейсы, Кинопоиск, Яндекс и VK отвечают `403 Forbidden`, просят пройти проверку или не грузятся совсем. Эти сервисы режут трафик с зарубежных IP и с адресов известных VPN-серверов.

Обычно советуют пустить весь российский интернет напрямую. Тогда мимо VPN уходит и то, что отлично работало бы с ним. Здесь наоборот: VPN остаётся включённым для всего, а напрямую идут только домены, которые с ним не открываются.

## Как это работает

1. Раз в 6 часов GitHub Actions собирает свежий список из нескольких открытых источников.
2. Клиент сам скачивает готовый файл в своём формате: Mihomo берёт `rule-provider`, Happ и Incy профиль с `geosite.dat`, sing-box свой rule-set.
3. Домены из списка идут через твой обычный интернет, остальное по правилам подписки, то есть через VPN.

Компьютер для обновления включать не нужно: сборка идёт на серверах GitHub.

## Быстрый старт

Выбери свой клиент:

| Клиент | Что использовать |
|---|---|
| FlClashX, Clash Verge, Koala Clash, Clash Mi и другие на Mihomo | [скрипт или `rule-provider`](#flclashx) |
| Happ, Incy | [профиль маршрутизации](#happ-и-incy) |
| Hiddify, Karing, NekoBox и другие на sing-box | [rule-set](#sing-box) |
| v2rayN, v2rayNG и другие на Xray | [`geosite.dat`](#xray-v2rayn-v2rayng) |

### FlClashX

1. Скопируй содержимое [`flclashx-ru-direct.js`](flclashx-ru-direct.js).
2. В FlClashX открой редактор скрипта профиля, вставь код и сохрани.
3. Обнови профиль.

Скрипт берёт списки из этого репозитория. Если хочешь свои правки, сделай форк и замени `GITHUB_USER` в начале скрипта на свой ник.

В начале скрипта есть настройка `LIST`: `"full"` (по умолчанию) или `"strict"`. Чем они различаются, написано ниже.

### Чистый Mihomo, Clash Meta, Clash Verge

Добавь в конфиг:

```yaml
rule-providers:
  ru-direct:
    type: http
    behavior: domain
    format: text
    url: https://raw.githubusercontent.com/kreip-zero/ru-vpn-direct-lists/main/ru-direct-full.txt
    path: ./ru-direct.txt
    interval: 21600

rules:
  - RULE-SET,ru-direct,DIRECT   # поставь выше остальных правил
```

Если GitHub в твоей сети открывается плохо, добавь в провайдер строку `proxy: <название твоей группы с VPN>`: тогда список скачается через VPN.

### Happ и Incy

Профиль маршрутизации ставится в одно касание. Открой ссылку на телефоне с установленным приложением:

| Клиент | Список `strict` | Список `full` |
|---|---|---|
| Happ | [`ru-direct-strict.deeplink`](clients/happ/ru-direct-strict.deeplink) | [`ru-direct-full.deeplink`](clients/happ/ru-direct-full.deeplink) |
| Incy | [`ru-direct-strict.deeplink`](clients/incy/ru-direct-strict.deeplink) | [`ru-direct-full.deeplink`](clients/incy/ru-direct-full.deeplink) |

Внутри файла одна строка вида `happ://routing/onadd/...` или `incy://routing/onadd/...`. Скопируй её и открой как ссылку (например, отправь себе в Telegram и нажми). Профиль подключится сам.

Если диплинк не сработал, рядом лежат те же настройки в JSON: [`clients/happ/`](clients/happ) и [`clients/incy/`](clients/incy). Профиль включает режим «весь трафик через VPN» и отправляет напрямую только домены из списка. Сам список подтягивается из `geosite/ru-direct.dat`, который обновляется вместе с остальными файлами.

Одна оговорка: профиль задаёт собственную маршрутизацию. Если у тебя уже настроен другой профиль в Happ или Incy, он будет заменён.

### sing-box

Для Hiddify, Karing, NekoBox и других клиентов на sing-box:

```json
{
  "route": {
    "rule_set": [
      {
        "type": "remote",
        "tag": "ru-direct",
        "format": "source",
        "url": "https://raw.githubusercontent.com/kreip-zero/ru-vpn-direct-lists/main/sing-box/ru-direct-full.json",
        "download_detour": "proxy",
        "update_interval": "6h"
      }
    ],
    "rules": [
      { "rule_set": "ru-direct", "outbound": "direct" }
    ]
  }
}
```

Правило поставь выше остальных. В `download_detour` укажи тег своего VPN-выхода (в примере `proxy`).

### Xray (v2rayN, v2rayNG)

Скачай [`geosite/ru-direct.dat`](geosite/ru-direct.dat) и положи рядом с обычным `geosite.dat` (или замени его, если используешь только это правило). В правилах маршрутизации укажи домен `geosite:RU-DIRECT-FULL` (или `geosite:RU-DIRECT-STRICT`) с выходом `direct`.

## Какой список выбрать

| Файл | Что внутри | Когда брать |
|---|---|---|
| `ru-direct-strict.txt` | Сайты, которые пускают только с российских IP, курируемый список hydraponique и твой `custom.txt`. Около 240 доменов | Хочешь минимум исключений из VPN |
| `ru-direct-full.txt` | Всё из `strict` плюс сервисы из UnRKN/ru-blocklist, которые режут или выдают VPN. Около 800 доменов | Нужно, чтобы работало как можно больше сервисов |

Начни со `strict`. Если что-то нужное не открывается, переключись на `full`.

## Файлы репозитория

| Файл | Назначение |
|---|---|
| `ru-direct-strict.txt`, `ru-direct-full.txt` | Готовые списки в формате Mihomo (`+.домен`, поддомены включены) |
| `geosite/ru-direct.dat` | Те же списки как `geosite.dat` с тегами `RU-DIRECT-STRICT` и `RU-DIRECT-FULL` (Happ, Incy, Xray) |
| `clients/happ/`, `clients/incy/` | Профили маршрутизации (JSON) и диплинки для установки в одно касание |
| `sing-box/` | Rule-set в формате `source` для клиентов на sing-box |
| `custom.txt` | Свои домены: добавил сюда сайт с 403, и после пересборки он идёт напрямую |
| `exclude.txt` | Домены, которые нужно убрать из списков (сам домен и все его поддомены) |
| `flclashx-ru-direct.js` | Готовый скрипт для FlClashX |
| `build.py` | Сборщик: скачивает источники, объединяет, убирает дубли |
| `sources/` | Последняя удачная копия каждого источника на случай, если он недоступен |
| `.github/workflows/update.yml` | Расписание автообновления |

## Сайт не открывается или открывается зря

- **Сайт даёт 403, а в списке его нет.** Добавь домен в `custom.txt` в своём форке. Для разовой правки без форка впиши его в `extraDirect` в скрипте. Если сайт нужен всем, открой Issue или Pull Request.
- **Сайт работает через VPN, но идёт напрямую.** Впиши домен в `exclude.txt`: он вернётся на VPN.

Пересборка запускается сама, когда меняется `custom.txt` или `exclude.txt`.

## Откуда данные

- [runetfreedom/russia-v2ray-rules-dat](https://github.com/runetfreedom/russia-v2ray-rules-dat): категория `ru-available-only-inside`, домены, доступные только с российских IP.
- [hydraponique/roscomvpn-geosite](https://github.com/hydraponique/roscomvpn-geosite): категория `category-ru`.
- [UnRKN/ru-blocklist](https://github.com/UnRKN/ru-blocklist): российские сервисы, которые не работают с VPN или сообщают о его использовании.

Домены принадлежат их авторам, здесь они собраны и приведены к одному формату. Если источник упал или вернул слишком мало данных, сборщик берёт его последнюю удачную копию из `sources/`.

## Что нужно знать

- Каждый сайт по отдельности никто не проверял. Списки собраны из чужих источников, поэтому в `full` могут попасть сервисы, которые на самом деле работают и через VPN. Для таких случаев есть `exclude.txt`.
- В списках только домены. Приложения, которые ходят на сервер по IP-адресу, они не затрагивают.
- Старый Clash (не Meta) формат `rule-provider` с доменами не поддерживает, нужен Mihomo.
- Профили для Happ, Incy и sing-box собраны по документации и по рабочим примерам других проектов. Я проверил, что файлы читаются обратно и совпадают со списками, но в самих приложениях пока не запускал. Если что-то не подхватилось, открой Issue.
- Сайты из списка видят твой настоящий IP. Так и задумано, иначе они бы не открылись.
