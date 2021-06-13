FROM rust:1.52.1 as builder

# Build ProtoSVG
WORKDIR /usr/src/protosvg
COPY ./src/protosvg .
RUN rustup component add rustfmt
RUN cargo install --locked --path .



FROM python:3.7

EXPOSE 8092
EXPOSE 50051

# System dependencies
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        libmagic1 \
        libraqm-dev \
        supervisor && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy the built ProtoSVG
COPY --from=builder /usr/local/cargo/bin/protosvg /usr/bin/protosvg

# Install PyTorch
RUN pip install torch==1.8.1+cpu torchvision==0.9.1+cpu torchaudio==0.8.1 -f https://download.pytorch.org/whl/torch_stable.html

# Install other Python libraries
COPY ./requirements.txt /inference-api/requirements.txt
RUN pip install -r /inference-api/requirements.txt

# Clone and build DiffVG
WORKDIR /tmp/builds
RUN git clone --recursive https://github.com/BachiLi/diffvg
RUN cd diffvg && python setup.py install
RUN rm -rf /tmp/builds

# Install the fonts
WORKDIR /tmp/fonts
COPY ./fonts.txt fonts.txt
RUN wget -i fonts.txt
RUN mv Neucha.ttf Neucha-Regular.ttf
RUN mv PT_Serif-Web-Bold.ttf PTSerif-Bold.ttf
RUN mv PT_Serif-Web-Regular.ttf PTSerif-Regular.ttf
RUN mv *.ttf /usr/share/fonts
RUN fc-cache -fv
RUN rm -rf /tmp/fonts

# Configure the supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Copy CoverGAN

# should be mounted as a volume
# COPY ./weights /inference-api/weights

COPY ./src/covergan /inference-api/covergan

WORKDIR /inference-api/covergan

# Copy backend files
COPY ./server.py ./server.py
COPY ./config.yml ./config.yml


# Run the processes
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
