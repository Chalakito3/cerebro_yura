# kNN-VC (copia mínima)

Código de https://github.com/bshall/knn-vc (licencia MIT, `LICENSE`), usado por
`basedatos/entrenar_voz_yura.py` para que Yura diga cada palabra quechua con la
pronunciación de los audios de la docente y con su propia voz.

Se copiaron solo `wavlm/` (WavLM, Microsoft, MIT) y `hifigan/models.py`,
`utils.py` y `config_v1_wavlm.json`. No se copió `matcher.py` porque usa
`torchaudio`, que no existe para la versión de torch instalada; su lógica
(vecinos más cercanos sobre la capa 6 de WavLM) está en `basedatos/entrenar_voz_yura.py`.
Los pesos (unos 1,3 GB) se descargan una vez en `~/.cache/torch/hub/checkpoints/`.
