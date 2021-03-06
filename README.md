# CoverGAN Inference Image

This contains configuration files and deployment scripts for the CoverGAN inference image.

## Build instructions
* Clone the repository:  
```sh
git clone --recursive git@github.com:IlyaBizyaev/covergan-inference.git
```
* Place model weights (`covergan.pt` and `captioner.pt`) in a subdirectory named `weights`
* Build the image:  
```sh
docker build --network=host -t "covergan-inference:Dockerfile" .

docker build -t covergan .
```

## Running
```sh
docker run -p 8080:8080 covergan-inference:Dockerfile

docker run -d --restart unless-stopped --network="host" -v "$(pwd)/weights:/inference-api/weights" --name covergan -t covergan
```

## Testing
Below is an example command that can be used to trigger the generation endpoint:

```sh
curl --progress-bar \
    -F "audio_file=@/home/user/audio.flac" \
    "http://localhost:8092/generate?track_artist=Cool%20Band&track_name=Song&emotion=joy" \
    -o ~/output.json
```
