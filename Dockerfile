# syntax=docker/dockerfile:1.4
FROM plone/plone-backend:5.2.7

# Installing with the `pip` shipped with Plone (21.2.4) is not working (the installation hangs)
USER root
#RUN /app/bin/pip install -U pip==22.0.4 

COPY . /jazkarta.shop
RUN /app/bin/pip install Products.PrintingMailHost /jazkarta.shop --use-deprecated legacy-resolver

RUN <<DOCKEREOF
cat >> /app/etc/zope.conf <<EOF
<zodb_db temporary>
    <temporarystorage>
      name temporary storage for sessioning
    </temporarystorage>
    mount-point /temp_folder
    container-class Products.TemporaryFolder.TemporaryContainer
</zodb_db>
EOF
DOCKEREOF
