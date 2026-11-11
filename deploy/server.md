# Сервер лендингов — что нужно для кнопки «Опубликовать»

Зона Романа: делает сам, со своим агентом или поручает Майку. Агент доступа к серверу не имеет.
Сервер только раздаёт готовые файлы: ни сборки, ни скриптов на нём нет.

## 1. Пользователь, который пишет только в папку сайта

```sh
sudo adduser --disabled-password --gecos "" landings
sudo install -d -o landings -g landings -m 755 /var/www/landings
```

Ключ — новый, только для публикации (на своём компьютере, без пароля):

```sh
ssh-keygen -t ed25519 -N "" -C "github-landings" -f landings_deploy
```

Открытую часть (`landings_deploy.pub`) — в `/home/landings/.ssh/authorized_keys` одной строкой, с ограничением
на одну папку (rrsync идёт с rsync: `/usr/bin/rrsync`, на старых системах — `/usr/share/doc/rsync/scripts/rrsync`):

```
command="/usr/bin/rrsync /var/www/landings",restrict ssh-ed25519 AAAA… github-landings
```

С таким ключом можно только записать файлы в `/var/www/landings` — ни команд, ни других папок.

## 2. Секреты в GitHub

Хранилище → Settings → Secrets and variables → Actions → New repository secret:

| Имя | Что |
|---|---|
| `DEPLOY_HOST` | адрес сервера |
| `DEPLOY_USER` | `landings` |
| `DEPLOY_KEY` | содержимое `landings_deploy` (закрытая часть, целиком). После — удалить файл с компьютера |
| `DEPLOY_KNOWN_HOSTS` | вывод `ssh-keyscan -t ed25519 <адрес сервера>` |
| `DEPLOY_PORT` | только если SSH не на 22 |

`DEPLOY_PATH` не нужен: при rrsync папка уже задана в ключе.

## 3. Веб-сервер с https

Пример для Caddy (сам выпускает сертификат):

```
ДОМЕН.RU {
	root * /var/www/landings
	@static path /shared/* */img/* /_catalog/*
	header @static Cache-Control "public, max-age=86400"
	header -Server
	encode zstd gzip
	file_server
}
```

Адреса страниц постоянные: `https://ДОМЕН.RU/<код>/` — на них ведут напечатанные QR-коды.

## Проверка

Actions → «Опубликовать» → Run workflow (ветка `main`). Зелёная галочка → открыть `https://ДОМЕН.RU/<код>/`.
