clear; clc; close all; clear all;
load('C:\Github\FAST\+DatabasePkg\IDEAS_DB.mat')

% TurbofanAC = rmfield(TurbofanAC,"EMB_135BJ");
% need to run in engine database validation flag

rng(10022024)

N = 100;
MeanErrors = zeros(N,1);
MeanStds   = zeros(N,1);
ErrorFastTest = [];

for ii = 1:N
    TurbofanAC = DatabasePkg.RandomizeDB(TurbofanAC,90);
    [Etemp] = OEW_Regressions(TurbofanAC,1);
    ErrorFastTest = [ErrorFastTest;Etemp];
end




%% Roskam and Raymer Regressions

RRIO = {["Specs","Weight","MTOW"],["Specs","Weight","OEW"]};
[RRmtow,RRoew] = ReturnTargetMatrix(TurbofanAC,RRIO);

% both want input in terms of pounds
RRmtow = UnitConversionPkg.ConvMass(RRmtow,'kg','lbm');

% Set Raymer Coeffs
a = 1.02;
C = -0.06;

% Raymer Regression
Raymer_oew = RRmtow.*(a.*RRmtow.^C);

% Convert Back to kilograms
Raymer_oew = UnitConversionPkg.ConvMass(Raymer_oew,'lbm','kg');

% Set Roskam Coeffs
A = 0.0833;
B = 1.0383;

% Roskam Regression
Roskam_oew = RRmtow.*10^(-A/B).*(RRmtow.^((1/B)-1));

% Convert Back to kilograms
Roskam_oew = UnitConversionPkg.ConvMass(Roskam_oew,'lbm','kg');

% Calculate Errors
Raymer_error = (Raymer_oew - RRoew)./RRoew.*100;
Roskam_error = (Roskam_oew - RRoew)./RRoew.*100;

% Calculate L2 Norms
RaymerL2 = sqrt(sum(Raymer_error.^2))/length(Raymer_error);
RoskamL2 = sqrt(sum(Roskam_error.^2))/length(Roskam_error);

%% Jenkinson Regression

% set IO space
JenkinsonIO = {["Specs","Weight","MTOW"],["Specs", "Propulsion", "NumEngines"],["Specs","Weight","OEW"]};
[Jinputs,JOEWS_True] = ReturnTargetMatrix(TurbofanAC,JenkinsonIO);

% Get input and output vectors
JMTOWs = Jinputs(:,1);
JNEng = Jinputs(:,2);

joewpred = (0.47 + mod(42,JNEng+3).*0.04).*JMTOWs;

% error calculation
jerror = (joewpred - JOEWS_True)./JOEWS_True.*100;

JenkinsonL2 = sqrt(sum(jerror.^2))/length(jerror);

%% Raymer Plots
figure(2) % Predicted vs Actual and error

% Predicted vs Actual
subplot(1,2,1)
hold on
scatter(RRoew,Raymer_oew,50,'m^')
plot([0 3e5],[0 3e5], 'k--','LineWidth', 1)
title('Predicted vs Actual OEW')
xlabel('Actual OEW (kg)')
ylabel ('Predicted OEW (kg)')
grid on
legend("Raymer","Y = X",'location','northwest')
ax = gca;
ax.FontSize = 12;
ax.FontName = "Times";

% errors
subplot(1,2,2)
hold on
scatter(RRoew,Raymer_error,50,'m^')
title('Error vs Actual OEW')
xlabel('Actual OEW (kg)')
ylabel ('Error (%)')
grid on
plot([0 3e5],[0 0], 'k--','LineWidth', 1)
legend("Raymer","0% error",'location','best')
ax = gca;
ax.FontSize = 12;
ax.FontName = "Times";

%% Roskam Plots

figure(3) % Predicted vs Actual and error

% Predicted vs Actual
subplot(1,2,1)
hold on
scatter(RRoew,Roskam_oew,50,'gsquare')
plot([0 3e5],[0 3e5], 'k--','LineWidth', 1)
title('Predicted vs Actual OEW')
xlabel('Actual OEW (kg)')
ylabel ('Predicted OEW (kg)')
grid on
legend("Roskam","Y = X",'location','northwest')
ax = gca;
ax.FontSize = 12;
ax.FontName = "Times";

% errors
subplot(1,2,2)
hold on
scatter(RRoew,Roskam_error,50,'gsquare')
title('Error vs Actual OEW')
xlabel('Actual OEW (kg)')
ylabel ('Error (%)')
grid on
plot([0 3e5],[0 0], 'k--','LineWidth', 1)
legend("Roskam","0% error",'location','best')
ax = gca;
ax.FontSize = 12;
ax.FontName = "Times";

%% Jenkinson Plots

figure(4) % Predicted vs Actual and error

% Predicted vs Actual
subplot(1,2,1)
hold on
scatter(JOEWS_True,joewpred,50,'r+')
plot([0 3e5],[0 3e5], 'k--','LineWidth', 1)
title('Predicted vs Actual OEW')
xlabel('Actual OEW (kg)')
ylabel ('Predicted OEW (kg)')
grid on
legend("Jenkinson","Y = X",'location','northwest')
ax = gca;
ax.FontSize = 12;
ax.FontName = "Times";

% errors
subplot(1,2,2)
hold on
scatter(JOEWS_True,jerror,50,'r+')
title('Error vs Actual OEW')
xlabel('Actual OEW (kg)')
ylabel ('Error (%)')
grid on
plot([0 3e5],[0 0], 'k--','LineWidth', 1)
legend("Jenkinson","0% error",'location','best')
ax = gca;
ax.FontSize = 12;
ax.FontName = "Times";


%% Add to FAST plots

IO_Strings = {["Specs","Weight","Payload"],["Specs","Performance","Range"],["Specs","Weight","MTOW"],["Specs","Propulsion","Thrust","SLS"],["Specs","Weight","Airframe"]};
[RangeAndMTOW,OEWS] = ReturnTargetMatrix(TurbofanAC,IO_Strings);
[RegResponse,~] = RegressionPkg.NLGPR(TurbofanAC,IO_Strings,RangeAndMTOW);

ErrorFastTrain = (RegResponse - OEWS) ./ OEWS.*100;




figure(1) % Predicted vs Actual and error

% Predicted vs Actual
subplot(1,2,1)
hold on
scatter(OEWS,RegResponse,50,'ko')
plot([0 3e5],[0 3e5], 'k--','LineWidth', 1)
title('Predicted vs Actual OEW')
xlabel('Actual OEW (kg)')
ylabel ('Predicted OEW (kg)')
grid on
CreateLegend(N,1)
ax = gca;
ax.FontSize = 12;
ax.FontName = "Times";

% errors
subplot(1,2,2)
hold on
scatter(OEWS,ErrorFastTrain,50,'ko')
title('Error vs Actual OEW')
xlabel('Actual OEW (kg)')
ylabel ('Error (%)')
grid on
plot([0 3e5],[0 0], 'k--','LineWidth', 1)
CreateLegend(N,2)
ax = gca;
ax.FontSize = 12;
ax.FontName = "Times";






%% Pic Formatting

set(figure(1),'position',[0,500,950,500])
set(figure(2),'position',[1100,700,900,500])
set(figure(3),'position',[10,0,900,500])
set(figure(4),'position',[700,0,900,500])

% print(figure(1),'../EAP/DB_Paper_Scripts/FastOEW','-dpdf')
% print(figure(2),'../EAP/DB_Paper_Scripts/RayOEW','-dpdf')
% print(figure(3),'../EAP/DB_Paper_Scripts/RoskOEW','-dpdf')
% print(figure(4),'../EAP/DB_Paper_Scripts/JenkOEW','-dpdf')
clc;

%% Table

Regnames = ["FAST (Test Data)","FAST (All Data)","Raymer","Jenkinson","Roskam"]';
Emeans = [mean(ErrorFastTest),mean(ErrorFastTrain),mean(Raymer_error),mean(jerror),mean(Roskam_error)]';
Emeds = [median(ErrorFastTest),median(ErrorFastTrain),median(Raymer_error),median(jerror),median(Roskam_error)]';
Estds =  [ std(ErrorFastTest),std(ErrorFastTrain), std(Raymer_error), std(jerror), std(Roskam_error)]';
Eskew =  [ skewness(ErrorFastTest),skewness(ErrorFastTrain), skewness(Raymer_error), skewness(jerror), skewness(Roskam_error)]';
Ekurt =  [ kurtosis(ErrorFastTest),kurtosis(ErrorFastTrain), kurtosis(Raymer_error), kurtosis(jerror), kurtosis(Roskam_error)]';
L2Tab = table(Regnames,Emeans,Emeds,Estds,Eskew,Ekurt,'VariableNames',["Regression","Mean","Median","Std. Dev.","Skew","Kurtosis"]);

L2Tab


%% Functions

function [] = CreateLegend(N,argin)

emptycell = cell(1,N);
for ii = 1:N
    emptycell{ii} = "";
end


switch argin
    case 1
        textcell = [emptycell(1:N-1),{"FAST 1","FAST 2","Y = X"}];
    case 2
        textcell = [emptycell(1:N-1),{"FAST 1","FAST 2","0% error"}];
end

legend(textcell,'location','best')


end

function [Target,TrueVals] = ReturnTargetMatrix(DataStructure,IOSpace)
% for a given IO this function will create the NaN-free list of true values
% and the target matrix which is the input to the NLGPR function
% Initialize and create datamatrix

if isempty(DataStructure)
    Target = [];
    TrueVals = [];
    return
end

DataMatrix = [];
for i = 1:length(IOSpace)
    [~,IOiMat] = RegressionPkg.SearchDB(DataStructure,IOSpace{i});
    DataMatrix = [DataMatrix,cell2mat(IOiMat(:,2))];
end
% remove NaNs
c = 1;
for i = 1:size(DataMatrix,1)
    for j = 1:size(DataMatrix,2)
        if isnan(DataMatrix(i,j))
            indexc(c) = i; c = c+1;
        end
    end
end
% if there were no NaNs (rare but possible) this just ignores the try
try
    DataMatrix(indexc,:) = [];
catch
end
% assign outputs
Target = DataMatrix(:,1:end-1);
TrueVals = DataMatrix(:,end);
end % ReturnTargetMatrix

function [Error] = OEW_Regressions(TurbofanAC,Plotting)


% set training and validation structures
[TrainingStructure,~] = RegressionPkg.SearchDB(TurbofanAC,["Settings","DataTypeValidation"],"Training");
[ValidationStructure,~] = RegressionPkg.SearchDB(TurbofanAC,["Settings","DataTypeValidation"],"Validation");


%% FAST Regression
IO_Strings = {["Specs","Weight","Payload"],["Specs","Performance","Range"],["Specs","Weight","MTOW"],["Specs","Propulsion","Thrust","SLS"],["Specs","Weight","Airframe"]};
[RangeAndMTOW,OEWS] = ReturnTargetMatrix(ValidationStructure,IO_Strings);
[RegResponse,~] = RegressionPkg.NLGPR(TrainingStructure,IO_Strings,RangeAndMTOW);

Error = (RegResponse - OEWS) ./ OEWS.*100;

%% Plots

if Plotting
figure(1) % actual vs predicted and error

% actual vs predicted
subplot(1,2,1)
hold on
scatter(OEWS,RegResponse,50,'co')

% errors
subplot(1,2,2)
hold on
scatter(OEWS,Error,50,'co')
end

end
