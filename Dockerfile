FROM python:3.10
WORKDIR /usr/src/app

RUN apt-get update && apt-get -y install cron

COPY requirements.txt .
RUN pip install -r ./requirements.txt

#Setting up cron clearing database

COPY ./cron_clear_db/cron /etc/cron.d/cron

RUN chmod 0644 /etc/cron.d/cron
RUN touch /var/log/cron.log

COPY . .

CMD ["sh", "-c", "cron && python main.py"] 

