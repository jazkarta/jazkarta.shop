FROM plone/plone-backend:5.2.7

COPY . /jazkarta.shop
# Installing with the `pip` shipped with Plone (21.2.4) is not working (the installation hangs)
USER root
RUN /app/bin/pip install -U pip==22.0.4 && /app/bin/pip install -e /jazkarta.shop
USER plone
