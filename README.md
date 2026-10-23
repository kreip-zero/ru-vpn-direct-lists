# ru-vpn-direct-lists

Автообновляемые списки сайтов, которые нужно открывать **в обход VPN** (DIRECT) в Clash/Mihomo/FlClashX. Всё остальное идёт через VPN.

Сборка идёт на серверах GitHub (Actions) каждые 6 часов, компьютер включать не нужно.

## Файлы

| Файл | Что внутри |
|---|---|
| `ru-direct-strict.txt` | Сайты, доступные только с российских IP (`geosite:ru-available-only-inside`), curated-список hydraponique и твой `custom.txt`. Самый точный список, ложных срабатываний минимум |
| `ru-direct-full.txt` | strict + [UnRKN/ru-blocklist](https://github.com/UnRKN/ru-blocklist) (сервисы, которые режут или палят VPN). Шире: часть сайтов может работать и через VPN |
| `custom.txt` | Твои домены. Добавь сюда сайт с 403: через несколько минут он пойдёт напрямую (пересборка запускается сама при изменении файла) |
| `exclude.txt` | Домены, которые нужно убрать из обоих списков (сам домен и поддомены) |

## Источники

- [runetfreedom/russia-v2ray-rules-dat](https://github.com/runetfreedom/russia-v2ray-rules-dat): `geosite:ru-available-only-inside`
- [hydraponique/roscomvpn-geosite](https://github.com/hydraponique/roscomvpn-geosite): `category-ru`
- [UnRKN/ru-blocklist](https://github.com/UnRKN/ru-blocklist): `ru-blocklist-ext.txt`

Если источник недоступен или вернул слишком мало данных, берётся его последняя удачная копия из `sources/`.

## Подключение в Mihomo

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
  - RULE-SET,ru-direct,DIRECT
```

В FlClashX проще использовать готовый скрипт `flclashx-ru-direct.js`.
