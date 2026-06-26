# AWA05 Emulation Environment
# Provides a reproducible container with QEMU + tools to run
# Raspberry Pi OS system emulation.
#
# This is the *launcher* environment. The actual Pi OS runs inside QEMU.

FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    qemu-system-aarch64 \
    qemu-utils \
    qemu-system-arm \
    libguestfs-tools \
    wget \
    xz-utils \
    curl \
    ca-certificates \
    unzip \
    file \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user (optional but nice)
RUN useradd -m -s /bin/bash awa05user && \
    echo "awa05user ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

WORKDIR /app

# Copy the emulation folder (will be overwritten by volume mount in compose)
COPY . /app/emulation

USER awa05user

CMD ["/bin/bash"]
