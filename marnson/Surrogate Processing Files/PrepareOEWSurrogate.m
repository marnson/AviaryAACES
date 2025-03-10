
%% Initialize and Load Database
clear;
clc;
close all;
load('+DatabasePkg/IDEAS_DB.mat')

%% Initialize Regression Processing Parameters

% Set datastruct as turbofan aircraft
DataStruct = TurbofanAC;

% Set input and output map
IOSpace = {["Specs","Weight","Payload"],...
           ["Specs","Performance","Range"],...
           ["Specs","Weight","MTOW"],...
           ["Specs","Propulsion","Thrust","SLS"],...
           ["Specs","Weight","Airframe"]};


% Use default options, simply mean prior and and equally weighted
% parameters
Options.Weights = ones(1,length(IOSpace)-1);
Options.Prior = 1 .* RegressionPkg.PriorCalculation(DataStruct,IOSpace);

% Run Preprocessing
[DataMatrix,HyperParams,InverseTerm] =...
RegressionPkg.RegProcessing(DataStruct,IOSpace, Options.Prior, Options.Weights);

%% Conversions to python variables
DataMatrixN = DataMatrix;
% DataMatrix = mat2str(DataMatrix);
% DataMatrix = strrep(DataMatrix, ' ', ',');
% DataMatrix = strrep(DataMatrix, ';', '],[');
% DataMatrix = ['[',DataMatrix,']'];

HyperParamsN = HyperParams;
% HyperParams = mat2str(HyperParams);
% HyperParams = strrep(HyperParams, ' ', ',');
% HyperParams = strrep(HyperParams, ';', '],[');
% HyperParams = ['[',HyperParams,']'];

InverseTermN = InverseTerm;
% InverseTerm = mat2str(InverseTerm);
% InverseTerm = strrep(InverseTerm, ' ', ',');
% InverseTerm = strrep(InverseTerm, ';', '],[');
% InverseTerm = ['[',InverseTerm,']'];



Mu0 = Options.Prior;

%% Save to Mat file


save('C:\Users\maxar\OneDrive - Umich\Python\AACES\RegressionData.mat','DataMatrix','InverseTerm','HyperParams','Mu0')


%% get an example output

Target = [20000, 3e6, 100e3 100e3];
RegressionPkg.BuildRegression(DataMatrixN,Options.Prior,Target,HyperParamsN,InverseTermN);











