FROM python:3.7

EXPOSE 8080

# System dependencies
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        ffmpeg \
        ssh \
        supervisor && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install PyTorch
RUN pip install torch==1.8.1+cpu torchvision==0.9.1+cpu torchaudio==0.8.1 -f https://download.pytorch.org/whl/torch_stable.html

# Install other Python libraries
COPY ./requirements.txt /inference-api/requirements.txt
RUN pip install -r /inference-api/requirements.txt

# Install Rust
ENV RUSTUP_HOME=/rust
ENV CARGO_HOME=/cargo 
ENV PATH=/cargo/bin:/rust/bin:$PATH
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --no-modify-path

# Clone and build DiffVG
WORKDIR /tmp/builds
RUN git clone --recursive https://github.com/BachiLi/diffvg
RUN cd diffvg && python setup.py install

# Copy and build ProtoSVG
COPY ./src/protosvg protosvg
RUN cd protosvg && cargo build --release && cp ./target/release/protosvg /usr/bin/
RUN rm -rf protosvg

# Install the fonts
WORKDIR /tmp/fonts
COPY ./fonts.txt fonts.txt
RUN wget -i fonts.txt
RUN mv PT_Serif-Web-Bold.ttf PTSerif-Bold.ttf
RUN mv PT_Serif-Web-Regular.ttf PTSerif-Regular.ttf
RUN mv *.ttf /usr/share/fonts
RUN fc-cache -fv

# Prepare the supervisor
RUN mkdir -p /var/log/supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Copy CoverGAN
COPY ./weights /inference-api/weights
COPY ./src/covergan /inference-api/covergan

WORKDIR /inference-api/covergan

# Copy backend files
COPY ./server.py ./server.py
COPY ./config.yml ./config.yml


# Run the processes
CMD ["/usr/bin/supervisord"]
