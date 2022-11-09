# OctopusEnergyMonitor

Octopus Energy Monitor using python fastapi javascript html css nginx

## Running in development

Needs a web server on the same port as 'origins' list in `main.py`
e.g. `python -m http.server 3000` from the static subdirectory
then run the server with `uvicorn main:app --reload`

The documentation for FastAPI endpoints can be read in the browser `http://localhost:8000/docs`

## Issues

On a mac, possibly other systems too, `main.js` is no reloaded automatically on changes (might be an issue with the python server) I had to use curl to request the main.js file.

```sh
curl http://localhost:3000/main.js
```

# run this server with: uvicorn main:app --reload

## Current issues

gunicorn doesn't start automatically (proably needs something else to start first?)
consumption is doing a network timeout

## Enhancements

Change config parsing from `ini` style to `toml` style as use `tomllib` will be included in 3.11 of python. `tomllib` is based on `https://github.com/hukkin/tomli` `pip install tomli`, so this can be used in the meantime.

/usr/local/var/log/unit/unit.log

## Deployment

remove `http://localhost:8000` from `main.js`

```nginx.conf
    location = / {
      try_files /index.html =404;
   }
```

[How to set index.html as root file in Nginx?](https://stackoverflow.com/questions/11954255/how-to-set-index-html-as-root-file-in-nginx)

nginx, gunicorn, nginx

[How can I make this try_files directive work?](https://stackoverflow.com/questions/17798457/how-can-i-make-this-try-files-directive-work)
[Uvicorn Deployment](https://www.uvicorn.org/deployment/#gunicorn)
[Deploying Gunicorn](https://docs.gunicorn.org/en/stable/deploy.html#nginx-configuration)

## Nginx Unit

replaces gunicorn, Uvicorn

```zsh
nunit --version
```
