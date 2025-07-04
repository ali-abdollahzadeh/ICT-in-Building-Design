# Base image
ARG UBUNTU_VER=22.04
ARG PY_VER=3.9

FROM ubuntu:${UBUNTU_VER}

# Imposta la modalità non interattiva per evitare prompt durante l'installazione
ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/root/miniconda3/bin:${PATH}"

# Installazione delle dipendenze di sistema essenziali
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl vim gcc g++ build-essential openjdk-11-jre git libarchive-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Installazione di Miniconda
RUN wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
    bash Miniconda3-latest-Linux-x86_64.sh -b -p /root/miniconda3 && \
    rm Miniconda3-latest-Linux-x86_64.sh && \
    conda clean -afy

# Installazione di Python e delle librerie richieste con conda e pip
RUN conda install -c anaconda -y python=${PY_VER} && \
    conda install -c conda-forge -y assimulo pyfmi && \
    conda install -c powerai -y gym && \
    conda install -y pip jupyter matplotlib && \
    pip install pandas paho-mqtt==1.6.1 cherrypy fastapi statsmodels flask ipykernel influxdb && \
    conda clean -afy

# Aggiunta del kernel Jupyter per l'ambiente Python corrente
RUN python -m ipykernel install --user --name "docker_env" --display-name "Python (${PY_VER}) - Docker"

# Installazione di EnergyPlus 9.4.0
ENV ENERGYPLUS_9_4_URL=https://github.com/NREL/EnergyPlus/releases/download/v9.4.0/EnergyPlus-9.4.0-998c4b761e-Linux-Ubuntu20.04-x86_64.sh
RUN wget -q $ENERGYPLUS_9_4_URL && \
    chmod +x EnergyPlus-9.4.0-998c4b761e-Linux-Ubuntu20.04-x86_64.sh && \
    echo "y" | ./EnergyPlus-9.4.0-998c4b761e-Linux-Ubuntu20.04-x86_64.sh && \
    rm EnergyPlus-9.4.0-998c4b761e-Linux-Ubuntu20.04-x86_64.sh && \
    rm -rf /usr/local/EnergyPlus-9-4-0/{DataSets,Documentation,ExampleFiles,WeatherData,MacroDataSets,PostProcess/convertESOMTRpgm,PostProcess/EP-Compare,PreProcess/FMUParser,PreProcess/ParametricPreProcessor,PreProcess/IDFVersionUpdater}

# Installazione di EnergyPlus 9.6.0
ENV ENERGYPLUS_9_6_URL=https://github.com/NREL/EnergyPlus/releases/download/v9.6.0/EnergyPlus-9.6.0-f420c06a69-Linux-Ubuntu20.04-x86_64.sh
RUN wget -q $ENERGYPLUS_9_6_URL && \
    chmod +x EnergyPlus-9.6.0-f420c06a69-Linux-Ubuntu20.04-x86_64.sh && \
    echo "y" | ./EnergyPlus-9.6.0-f420c06a69-Linux-Ubuntu20.04-x86_64.sh && \
    rm EnergyPlus-9.6.0-f420c06a69-Linux-Ubuntu20.04-x86_64.sh && \
    rm -rf /usr/local/EnergyPlus-9-6-0/{DataSets,Documentation,ExampleFiles,WeatherData,MacroDataSets,PostProcess/convertESOMTRpgm,PostProcess/EP-Compare,PreProcess/FMUParser,PreProcess/ParametricPreProcessor}

# Assicurarsi che entrambe le versioni di EnergyPlus siano nel PATH
ENV PATH="/usr/local/EnergyPlus-9-4-0:${PATH}"
ENV PATH="/usr/local/EnergyPlus-9-6-0:${PATH}"
ENV PATH="/usr/local:${PATH}"

# Copia delle directory dell'applicazione necessarie

COPY ./src/FMI-MLC /app/FMI-MLC

# Installazione di FMI-MLC
WORKDIR /app/FMI-MLC
RUN pip install . && \
    rm -rf /app/FMI-MLC


# Imposta la directory di lavoro su /app
WORKDIR /app
COPY ./src/EnergyPlusToFMU-v3.1.0 /app/EnergyPlusToFMU
# Esponi la porta per Jupyter Notebook
EXPOSE 8888

# Comando predefinito per avviare Jupyter Notebook
CMD ["jupyter", "notebook", "--port=8888", "--no-browser", "--ip=0.0.0.0", "--allow-root", "--NotebookApp.token=''", "--NotebookApp.password=''"]
