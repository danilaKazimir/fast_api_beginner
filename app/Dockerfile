FROM python:3.12.0

ENV HOME=/home/fast \
    APP_HOME=/home/fast/app \
    PYTHONPATH="$PYTHONPATH:/home/fast" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# создаём группу/пользователя и директории
RUN mkdir -p $APP_HOME \
 && groupadd -r fast \
 && useradd -r -g fast -d /home/fast fast

# работаем прямо в папке приложения
WORKDIR $APP_HOME

# сначала копируем requirements для кэша слоёв
COPY requirements.txt ./requirements.txt

RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# затем копируем остальной код (обратите внимание на слэш в конце)
COPY app/ .

# если alembic.ini нужен в $HOME, кладём его туда явно
COPY alembic.ini $HOME/

# права владельца
RUN chown -R fast:fast $HOME

USER fast
