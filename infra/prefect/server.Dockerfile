FROM prefecthq/prefect:3-latest


RUN apt-get update && apt-get install -y --no-install-recommends curl

# Script qui récupère l'URL au démarrage du conteneur
COPY infra/prefect/server-entrypoint.sh /server-entrypoint.sh
COPY infra/prefect/server-entrypoint.lib.sh /opt/prefect/server-entrypoint.lib.sh
COPY infra/prefect/scripts /opt/prefect/scripts
RUN chmod +x /server-entrypoint.sh /opt/prefect/server-entrypoint.lib.sh

ENTRYPOINT ["/server-entrypoint.sh"]