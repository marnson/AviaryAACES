% Requires to be run in a specific branch of FAST: engine database
% validation flag
% 
% Engine-Database-Validation-Flag
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


%% Auxiliary Functions


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

