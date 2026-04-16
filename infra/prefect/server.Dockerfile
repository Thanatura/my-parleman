FROM prefecthq/prefect:3-latest


RUN apt-get update && apt-get install -y --no-install-recommends curl

# Script qui récupère l'URL au démarrage du conteneur
COPY infra/prefect/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]