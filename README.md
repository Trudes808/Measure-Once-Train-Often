DISTRIBUTION STATEMENT A. Approved for public release. Distribution is unlimited.\\
This material is based upon work supported under Air Force Contract No. FA8702-15-D-0001. Any opinions, findings, conclusions, or recommendations expressed in this material are those of the author(s) and do not necessarily reflect the views of the U.S. Air Force.\\
© 2026 Massachusetts Institute of Technology.\\
Delivered to the U.S. Government with Unlimited Rights, as defined in DFARS Part 252.227-7013 or 7014 (Feb 2014). Notwithstanding any copyright notice, U.S. Government rights in this work are defined by DFARS 252.227-7013 or DFARS 252.227-7014 as detailed above. Use of this work other than as specifically authorized by the U.S. Government may violate any copyrights that exist in this work.

# CMAT: Channel-Measurement–Augmented Training

Deep learning models for RF signal classification often suffer from a **synthetic-to-real gap**: high accuracy in simulation but degraded performance in real-world deployments due to unseen channel conditions. **CMAT (Channel-Measurement–Augmented Training)** addresses this by decoupling channel capture from waveform collection. Using a brief OFDM sounding pass, CMAT records a small library of channel impulse responses (CIRs) at a deployment site. These measured channels are then convolved offline with clean synthetic waveforms to generate site-specific training data—without retransmitting each class over the air. This *“measure once, train often”* workflow enables scalable dataset generation, recovers much of the real-world accuracy loss, and allows new waveform classes to be added without recollecting field data.

---

## Citation
S. Trudeau, S. Chun, B. Nguyen, and K. Chowdhury, “Measure Once, Train Often: Scaling Waveform Classifiers with Channel-Augmented Data,” in Proc. IEEE/IFIP International Symposium on Modeling and Optimization in Mobile, Ad Hoc, and Wireless Networks (WiOpt), Columbus, OH, USA, 2026.

---

# T-PRIME Extension

This repository extends the original [T-PRIME](https://github.com/genesys-neu/t-prime-ext) project by adding CMAT-based channel augmentation and additional features for improved real-world RF signal classification.

---

## Installation

Before getting started, make sure you have the required dependencies installed.  

1. Clone the T-PRIME repository:
```bash
git clone https://github.com/genesys-neu/t-prime-ext.git
cd t-prime-ext/
```

2. Create a Conda environment and install the required packages:
```
conda env create --name t-prime --file ./conda-envs/TPrime_conda_env_training__nobuilds.yaml
```
> **Note:** If you encounter dependency issues during environment setup, try using the environment file at `Measure-Once-Train-Often/conda-envs/TPrime_conda_env_training__nobuilds.yaml`.

3. Activate the newly created Conda environment:
```
conda activate t-prime
```
4. Integrating CMAT with T-PRIME

Several files from the original T-PRIME repository have been modified or replaced to enable CMAT. These updated files are provided in this repository in the `Measure-Once-Train-Often/TPRIME_implementation` directory. 
### Files to copy from Measure-Once-Train-Often/TPRIME_implementation

Copy the following updated files into your cloned T-PRIME repository, preserving the directory structure:

- Measure-Once-Train-Often/TPRIME_implementation/baseline_models/model_cnn1d.py  
- Measure-Once-Train-Often/TPRIME_implementation/baseline_models/model_MCFormer.py  
- Measure-Once-Train-Often/TPRIME_implementation/baseline_models/TPrime_torch_train.py  
- Measure-Once-Train-Often/TPRIME_implementation/conda-envs/TPrime_conda_env_training__nobuilds.yaml  
- Measure-Once-Train-Often/TPRIME_implementation/preprocessing/TPrime_dataset.py  
- Measure-Once-Train-Often/TPRIME_implementation/TPrime_transformer/model_transformer.py  
- Measure-Once-Train-Often/TPRIME_implementation/TPrime_transformer/TPrime_transformer_train.py

```
git clone https://llcad-github.llan.ll.mit.edu/chuns/Measure-Once-Train-Often.git
cd Measure-Once-Train-Often
```

### Summary of Modifications
- Integrated CMAT support
- Implemented CFO sweep capability
- Added SNR sweep functionality
- Expanded protocol/class options
- Updated window generation logic
- Made the number of classes configurable


# Datasets
The datasets can be downloaded from [here](add_link).

```
cd t-prime-ext/
git clone https://llcad-github.llan.ll.mit.edu/chuns/DATASETS.git
```

### Simulated data
The synthetic datasets are organized as follows in the downloaded repository:

- `SYNTHETIC_DATASETS/MAIN/`  
  - Contains 10,000 `.mat` files per modulation class for training.
- `SYNTHETIC_DATASETS/SMALL/`  
  - Contains 100 `.mat` files per class, suitable for testing and quick experiments.
- `SYNTHETIC_DATASETS/12_CLASSES/`  
  - Extended dataset with 12 classes, including 4 additional protocols.

Each `.mat` file holds IQ samples for a specific modulation type.  
To use these datasets for training, set the `--raw_path` argument to the appropriate folder, e.g.:
```
--raw_path=../SYNTHETIC_DATASETS/MAIN
```
or for the extended set:
```
--raw_path=../SYNTHETIC_DATASETS/12_CLASSES
```

Place the above datasets in `Measure-Once-Train-Often/data`. You can specify this path in your training script using the `--raw_path` argument.


### Channel Estimations
The channel estimations are used in training to augment our synthetic datasets to simulate transmission over a certain channel/environment.
Download the relevant channel folders from the datasets repository (e.g., `wired`, `OTA10`, etc.).
During training, specify the desired channel environment using the `--channel_path` flag, e.g.:
```
--channel_path=../DATASETS/CHANNEL_ESTIMATES/wired
```
This allows you to select the appropriate channel augmentation for your experiments.

# Training procedure
##### Transformer models
All T-PRIME specific transformer models are in the `TPrime_transformer/` folder. The main script `TPrime_transformer_train.py` can be used to train T-PRIME transformer architectures as follows:
```
usage: TPrime_transformer_train.py [-h] [--snr_db SNR_DB [SNR_DB ...]] [--useRay] [--num-workers NUM_WORKERS] [--use-gpu] [--address ADDRESS] [--test] [--wchannel WCHANNEL] 
                                   [--raw_path RAW_PATH] [--cp_path CP_PATH] [--cls_token] [--dataset_ratio DATASET_RATIO] [--Layers LAYERS] [--Epochs EPOCHS] [--Learning_rate LEARNING_RATE] 
                                   [--Batch_size BATCH_SIZE] [--Slice_length SLICE_LENGTH] [--Sequence_length SEQUENCE_LENGTH] [--Positional_encoder POSITIONAL_ENCODER]
                                   [--channel_path CHANNEL_PATH] [--use_sota] [--sota_type SOTA_TYPE] [--use_cfo] [--max_cfo MAX_CFO] [--protocols PROTOCOLS]

```
### Example 
Wired Channel Augmentation with 8 classes implementation of T-PRIME can be reproduced and trained with the following command:
- Wired
```
python3 TPrime_transformer_train.py --wchannel=None --snr_db=30 --use-gpu --postfix=8classes --Layers=6 --Epochs=120 --Learning_rate=0.0002 --Batch_size=122 --Slice_length=64 --Sequence_length=16  --Positional_encoder=True --use_channel_aug --cp_path=../checkpoints/transformer/wired --raw_path=../DATASETS/SYNTHETIC_DATASETS/MAIN --channel_path=../DATASETS/CHANNEL_ESTIMATES/wired --protocols 16QAM 64QAM 8PSK BPSK CPFSK GFSK PAM4 QPSK
```
- OTA2 Channel Augmentation with 9 classes with awgn and snr sweeps implementations of T-PRIME can be reproduced and trained with the following command:
```
python3 TPrime_transformer_train.py --wchannel=None --snr_db=30 --use-gpu --postfix=9classes --Layers=6 --Epochs=120 --Learning_rate=0.0002 --Batch_size=122 --Slice_length=64 --Sequence_length=16  --Positional_encoder=True --use_channel_aug --cp_path=../checkpoints/transformer/wired --raw_path=../DATASETS/SYNTHETIC_DATASETS/MAIN --channel_path=../DATASETS/CHANNEL_ESTIMATES/ota10 --use_cfo --max_cfo=1000 --use_sota --sota_type=awgn --protocols 16QAM 64QAM 8PSK BPSK CPFSK GFSK PAM4 QPSK 802.11ax
```

###### Arguments description
```
  -h, --help            show this help message and exit
  --snr_db SNR_DB [SNR_DB ...]
                        SNR levels to be considered during training. It's possible to define multiple noise levels to be chosen at random during input slices generation. (default: [30])
  --useRay              Run with Ray's Trainer function (default: False)
  --num-workers NUM_WORKERS, -n NUM_WORKERS
                        Sets number of workers for training. (default: 2)
  --use-gpu             Enables GPU training (default: False)
  --address ADDRESS     the address to use for Ray (default: None)
  --test                Testing the model (default: False)
  --wchannel WCHANNEL   Wireless channel to be applied, it can beTGn, TGax, Rayleigh, relative or random. (default: None)
  --raw_path RAW_PATH   Path where raw signals are stored. (default: ../data/DATASET1_1)
  --cp_path CP_PATH     Path to the checkpoint to save/load the model. (default: ./model_cp)
  --cls_token           Use the Transformer v2 (default: False)
  --dataset_ratio DATASET_RATIO
                        Portion of the dataset used for training and validation. (default: 1.0)
  --Layers LAYERS
  --Epochs EPOCHS
  --Learning_rate LEARNING_RATE
  --Batch_size BATCH_SIZE
  --Slice_length SLICE_LENGTH
                        Slice length in which a sequence is divided. (default: 128)
  --Sequence_length SEQUENCE_LENGTH
                        Sequence length to input to the transformer. (default: 64)
  --Positional_encoder POSITIONAL_ENCODER

  --use_channel_aug      Run with CMAT augmentation (default: False)
  --channel_path         Path to CMAT channel (default = wired)
  --use_sota             Run with SOTA applied in training (default: 'awgn')
  --sota_type            Choose  
  --use_cfo              Run with CFO sweep (default: False)
  --max_cfo              CFO sweep max in hz (default: 2000)
  --protocols            PROTOCOLS (default: '16QAM', '64QAM', '8PSK', 'BPSK',
                        'CPFSK', 'GFSK', 'PAM4', 'QPSK')

```


## Testing with Real Collected Datasets

Once your models are trained, you can evaluate their performance using real collected datasets from the datasets repository.  
Under `REAL_RX`, you'll find datasets corresponding to various channel environments. These contain real receiver captures of unseen waveforms, providing a robust test set for model generalization.

To test your trained model, set the `--raw_path` argument to the appropriate `REAL_RX` dataset folder. For example:
```
--raw_path=../REAL_RX/wired
```
or
```
--raw_path=../REAL_RX/OTA10
```

This allows you to assess model accuracy and robustness on real-world data, ensuring your classifier performs well beyond synthetic and augmented datasets.


# Collecting Your Own Dataset (Measure Once, Train Often)
In addition to using the provided datasets, this repository supports collecting **your own environment-specific data**  to build your own dataset with custom channel measurements and waveform classes. The repo is based on the [NI RF Data Recording API](https://github.com/genesys-neu/ni-rf-data-recording-api), originally developed by NI and Northeastern University.  

While the original API focused on recording and replaying standard LTE/NR/WiFi/Radar waveforms, this fork extends functionality to:

- Transmit **MATLAB-generated waveforms** for modulation classification.  
- Run a **Tx/Rx chain with two radios** (X310/X410).  
- Save datasets in **SigMF format** for later signal processing and channel estimation.   

---



## Features Added in This Repo

- **Custom File Transmission**  
  - Support for transmitting the `.mat`, files containing IQ samples of our waveforms.  
  - MATLAB-generated signals can be replayed directly over the USRP.  
 
- **MATLAB Waveform Integration**  
  - A `src/configs/matwaves/` directory for custom classifier waveforms.  
  - Dedicated configs for each waveform class.  

- **OFDM Channel Estimation**
  - MATLAB Implementation of End to End Channel Estimation


## Requirements

### Software
- Ubuntu 20.04+  
- Python 3.9 (tested)  
- UHD with Python bindings  
- Python dependencies
- see https://github.com/genesys-neu/ni-rf-data-recording-api/blob/main/build/docker/README.md for Installing Dependencies and Run the API using Docker
  

### Hardware
- At least two USRPs (tested on **X310**, also compatible with **X410**)  
- Host PC with 10GbE recommended  
- SMA cables, attenuators for cabled setup  

Check connectivity with:
uhd_find_devices

---
# Transmitting MATLAB Waveforms for Classifier Training

This fork adds support for transmitting **MATLAB-generated waveforms** directly over the radios in order to build training datasets for modulation classification.

---

### Waveforms
Waveforms are stored under `src/waveforms/matwaves`, organized by class.  
Each class folder must include:
- A `.mat` file containing IQ samples (stored under the key `f_sig`).  
- A `.yaml` configuration file with the same base name.  

**Example:**
- IQ data: `8PSK.mat`  
- Config: `8PSK.yaml`  

---

### Configurations
Transmission and reception parameters are defined in `src/config`.  
- Example JSON configs for MATLAB waveforms are in subfolders like `matlabconfigs_xxx/`.  
- Each JSON config specifies parameters such as center frequency, sample rate, gain, duration, and save path.  

---

### Running the Transmit/Receive Chain
To transmit and record a MATLAB waveform, run:

```bash
cd src
python3 main_rf_data_recording_api.py --config path_to/Measure-Once-Train-Often/src/config/matlabconfigs_mdl/OFDM.json
```

### Results
The receiver saves the recorded data to the path declared in the config file. For example in the above config file saves to:
    Measure-Once-Train-Often/datatest_mdl/OFDM

### Make inference set
The script `make_inference_set.py` randomly selects IQ sample windows of length 1024 from each `sigmf-data` file in your collected dataset to build an inference/test set for post-training evaluation. Each output file contains a single window, ensuring samples are representative and non-overlapping.

**Usage Example:**
```bash
python3 Measure-Once-Train-Often/make_inference_set.py 
```
Set parameters to 
- `input_root`: Directory containing your collected `.mat` files.
- `output_root`: Destination for the generated inference set.
- `window_length`: Length of each sample window (default: 1024).
- `num_windows_per_file`: Number of random windows to extract per file.

This prepares a standardized test set for model evaluation.

# OFDM Channel Estimation Process

Channel estimation is performed using a known OFDM packet. The overall workflow consists of transmitting a reference waveform, extracting synchronized packet snippets, and running MATLAB scripts to generate channel impulse responses.

---

### 1. Transmit Known OFDM Waveform
- Use the provided reference waveform:  
  `src/waveforms/matwaves/OFDM/OFDM.mat`  
- Transmit it over the air using:  
  `main_rf_data_recording_api.py`

---

### 2. Extract Packet Snippets (Python)
- Match filter the received signal with the sync sequence of the transmitted OFDM waveform.  
- Extract packet snippets to be used for channel estimation in MATLAB.  

Use the script `Measure-Once-Train-Often/get_snips_for_channelest.py` with the following settings:
- `RSSpacing` → Change from 2 to 1
- `tx_path` → path to the transmitted `OFDM.mat` file.  
- `folder_path` → path to the received data folder.  
- `output_path` → destination directory for saving the extracted snippets (to be imported into MATLAB).  

---

### 3. MATLAB: Generate Channel Impulse Responses
1. Download the repository:  
   `Measure-Once-Train-Often/OFDMEndToEndExample` into MATLAB.  

2. Place the **match-filtered receive snippets** into the same folder.  

3. Open `OFDMEndToEndExample.mlx` and update line 115:  
   ```matlab
   matFile = fullfile('output_path', sprintf('%d.mat', fileIdx));
Change output_path to the name of the folder of your match filtered receive symbols.

- The above script calls helperOFDMChannelEstimation.m which then saves single frame channel estimates to 'estimated_chans' which are .mat files with key 'chanEstCurrent' 
On line 37 outputDir = 'Estimated Channels'; change to the path you want to save folder of channel estimates.

- Run `OFDMEndToEndExample.mlx` with 'BWIndex' == 5 and 'numFrames' to number of recieve symbols you have. 
