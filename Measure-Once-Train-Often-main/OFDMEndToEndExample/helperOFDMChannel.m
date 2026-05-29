function rxOut = helperOFDMChannel(txIn,chanParam,sysParam)
%helperOFDMChannel() Generate channel impairments.
%   This function generates channel impairments and applies them to the
%   input waveform.
%   rxOut = helperOFDMChannel(txIn,chanParam,sysParam)
%   txIn - input time-domain waveform
%   chanParam - structure of channel impairment parameters
%   sysParam - structure of system parameters
%   rxOut - output time-domain waveform
%
%   The channel parameters specify the level of impairments:
%
%   Normalized Doppler shift - Doppler frequency times symbol duration
%   Path delays and gains - Vector of path delays and average gains
%   SNR - in dB
%   Normalized carrier frequency offset (ppm) - tx/rx frequency offset
%   divided by the sample rate. Though processing is done in the baseband, it
%   is assumed that carrier offset is preserved when down-converting to DC. 

% Copyright 2022 The MathWorks, Inc.

symLen = (sysParam.FFTLen+sysParam.CPLen);

% Create a persistent channel filter object for channel fading
persistent rayChan;
if isempty(rayChan)
    Ts = 1/(sysParam.scs*sysParam.FFTLen);  % sample period
    T = symLen*Ts;                          % symbol duration (s)
    fmax = chanParam.doppler/T;
    rayChan = comm.RayleighChannel( ...
        SampleRate=1/Ts, ...
        PathDelays=chanParam.pathDelay, ...
        AveragePathGains=chanParam.pathGain, ...
        MaximumDopplerShift=fmax, ...
        Visualization=sysParam.chanVisual);
end

persistent pfo;
if isempty(pfo)
    pfo = comm.PhaseFrequencyOffset(...
        SampleRate=1e6, ...    % Phase-frequency offset is specified in PPM
        FrequencyOffsetSource="Input port");
end

% Rayleigh fading channel
if sysParam.enableFading
    fadingChanOut = rayChan(txIn);
else
    fadingChanOut = txIn;
end

% AWGN
txScaleFactor = sysParam.usedSubCarr/(sysParam.FFTLen^2);
signalPowerDbW = 10*log10(txScaleFactor);
rxChanOut = awgn(fadingChanOut,chanParam.SNR,signalPowerDbW);

% Carrier frequency offset
rxOut = pfo(rxChanOut,chanParam.foff);

end

