import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.decomposition import PCA
from sklearn.preprocessing import OneHotEncoder, LabelEncoder
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
from sklearn import svm
from sklearn.ensemble import RandomForestRegressor
from sklearn.neighbors import KNeighborsRegressor

#############################
### IMPORT SAMPLE of DATA ###
#############################

data=r'C:\Users\joogl\InsuranceClaimPredictions_Data\train_set.csv'
df = pd.read_csv(data, nrows=100000)
df.head(10)

#####################
### Summary Stats ###
#####################

df_nz = df['Claim_Amount'][df['Claim_Amount']!=0]
print('Claim amount: min: {}, max: {}, mean: {}, sd: {}'.format(
    round(df_nz.min(), 2),
    round(df_nz.max(), 2),
    round(df_nz.mean(), 2),
    round(df_nz.std(), 2)
))

####################
### Prepare Data ###
####################

# dummy code claims
df['claim'] = df.Claim_Amount.apply(lambda x: 0 if x == 0 else 1)
df['Model_Year'] = df['Model_Year'] - np.min(df['Model_Year'])
df['Model_Year'] = df['Model_Year'].astype('float64')
df.head()

# separate feature matrix from labels (claims in {0 = No claim, 1 = Claim})
# only continuous variables are included in the model
X = df[['Var5', 'Var6', 'Var7', 'Var8', 'NVVar1', 'NVVar2', 'NVVar3', 'NVVar4', 'Vehicle', 'Model_Year', 'Blind_Submodel']]
y = df[['claim', 'Claim_Amount']].values

# split data into train and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.25, random_state = 42)


###############################################################
### One-Hot Encode Non-Continuous Data and Prepare PCA Vars ###
###############################################################

def pipeline(X):
    df_cont = pd.DataFrame()
    df_cat = pd.DataFrame()
    for x in X:
        if X[x].dtypes == 'float64':
            df_cont['{}'.format(x)] = X[x]
        else:
            df_cat['{}'.format(x)] = X[x]

    dummy = OneHotEncoder()
    dummyC = LabelEncoder()

    df_cat2 = np.zeros((df_cat.shape[0], 1))
    for x in df_cat:
        y = dummyC.fit_transform(df_cat[x].reshape(-1, 1))
        y = dummy.fit_transform(y.reshape(-1, 1)).toarray()
        y = pd.DataFrame(y[:, 1:])
        df_cat2 = np.hstack((df_cat2, y))
    df_cat = pd.DataFrame(df_cat2)

    pca = PCA(n_components=10)
    pca.fit_transform(df_cat)
    k = np.argmax(np.cumsum(pca.explained_variance_ratio_) > 0.95) + 1
    pca = PCA(n_components=k)
    df_cat_pca = pca.fit_transform(df_cat)
    df_cat = pd.DataFrame(df_cat_pca)

    return df_cont, df_cat

########################
### Prepare PCA Data ###
########################

X_train_cont, X_train_cat = pipeline(X_train)
X_test_cont, X_test_cat = pipeline(X_test)

# scale features to have same variance
sc = StandardScaler()
X_train_cont = sc.fit_transform(X_train_cont)
X_test_cont = sc.transform(X_test_cont)

X_train = pd.concat([pd.DataFrame(X_train_cont), pd.DataFrame(X_train_cat)], axis=1)
X_test = pd.concat([pd.DataFrame(X_test_cont), pd.DataFrame(X_test_cat)], axis=1)

########################################
### Declare and Run 1st Layer Models ###
########################################

def create_model(model, X, y):
    if model == 'lr':
        myModel = LogisticRegression(random_state=42, class_weight='balanced', n_jobs=-1)
    elif model == 'svm':
        myModel = SVC(kernel='linear', random_state=42, class_weight='balanced', cache_size=2048)
    elif model == 'rf':
        myModel = RandomForestClassifier(random_state=42, class_weight='balanced', n_jobs=-1)
    else:
        raise error('cannot fit that model')

    myModel.fit(X, y)

    y_pred = myModel.predict(X)
    in_acc = accuracy_score(y_pred, y)
    tn, fp, fn, tp = confusion_matrix(y_pred, y).ravel()
    print('Accuracy: {}, Precision: {}, Recall: {}'.format(round(in_acc, 2), tp / (tp + fp), tp / (tp + fn)))
    print(pd.DataFrame(confusion_matrix(y_pred, y)))

    return y_pred

pred1 = create_model('lr', X_train, y_train[:,0])
pred2 = create_model('svm', X_train, y_train[:,0])
pred3 = create_model('rf', X_train, y_train[:,0])

lr_pred = pd.Series(pred1 * 0.67)
svm_pred = pd.Series(pred2 * 0.79)
rf_pred = pd.Series(pred3 * 0.96)

##########################################################################
### Prepare Confusion Matrix to Analyze Type-I and Type-II Error Rates ###
##########################################################################

final_pred = pd.DataFrame([lr_pred, svm_pred, rf_pred]).sum()
final_pred = final_pred.apply(lambda x: 1 if x > 1 else 0)
in_acc = accuracy_score(final_pred, y_train[:,0])
tn, fp, fn, tp = confusion_matrix(final_pred, y_train[:,0]).ravel()
print('Accuracy: {}, Precision: {}, Recall: {}'.format(round(in_acc, 2), tp / (tp + fp), tp / (tp + fn)))
confusion_matrix(final_pred, y_train[:,0])

y_pred = model.predict(X_test)
out_acc = accuracy_score(y_pred, y_test[:,0])
tn, fp, fn, tp = confusion_matrix(y_pred, y_test[:,0]).ravel()
print('In-sample accuracy: {}, Precision: {}, Recall: {}'.format(round(out_acc, 2), tp / (tp + fp), tp / (tp + fn)))
confusion_matrix(y_pred, y_test[:,0])

X_train_claims = X_train[y_train[:,0] == 1]
y_train_claims = y_train[y_train[:,1] != 0, 1]
y_train_claims = np.log(1 + y_train_claims)

X_test_claims = X_test[y_test[:,0] == 1]
y_test_claims = y_test[y_test[:,1] != 0, 1]
y_test_claims = np.log(1 + y_test_claims)

plt.hist(y_train_claims)

########################################
### Declare and Run 2nd Layer Models ###
########################################

from sklearn.ensemble import RandomForestRegressor

regr = RandomForestRegressor(random_state=42)
regr.fit(X_train_claims, y_train_claims)

# get in and out of sample accuracy
y_pred = regr.predict(X_train_claims)
in_RMSE = np.sqrt(mean_squared_error(y_pred, y_train_claims))
y_pred = regr.predict(X_test_claims)
out_RMSE = np.sqrt(mean_squared_error(y_pred, y_test_claims))
rSquared = regr.score(X_train_claims, y_train_claims)
print('In-sample RMSE: {}\nOut-of-sample RMSE: {}\nRsquared: {}'.format(in_RMSE, out_RMSE, rSquared))

RMSEDollars = np.sqrt(mean_squared_error(np.expm1(regr.predict(X_train_claims)), np.expm1(y_train_claims)))
print('RMSE in US$:', RMSEDollars)
RMSEDollars = np.sqrt(mean_squared_error(np.expm1(regr.predict(X_test_claims)), np.expm1(y_test_claims)))
print('RMSE in US$:', RMSEDollars)

model1 = RandomForestClassifier(random_state=42, class_weight='balanced')
model1.fit(X_train, y_train[:,0])

model2 = RandomForestRegressor(random_state=42)
model2.fit(X_train_claims, y_train_claims)

def join_predict(model1, model2, X, y_cat, y_cont):
    print('clasifying (layer1)...')

    layer1 = model1.predict(X)

    print('regressing (layer2)...')
    X2 = X[layer1 != 0]
    print('Length of layer 2 :', len(X2))
    y2 = y_cont[layer1 != 0]
    layer2 = model2.predict(X2)

    layer1[layer1 != 0] = layer2

    print('done!')

    return layer1

y_pred_train = join_predict(model1, model2, X_train, y_train[:,0], np.log(1 + y_train[:,1]))

# get prediction error
in_RMSE = np.sqrt(mean_squared_error(y_pred_train, np.log(1 + y_train[:,1])))
rSquared = regr.score(X_train, np.log(1 + y_train[:,1]))
print('RMSE: {}\nRsquared: {}'.format(in_RMSE, rSquared))

acc = np.sqrt(mean_squared_error(y_pred_train, np.log(1 + y_train[:, 1])))
print('Final model accuracy on train set (in log):', acc)
print('Error for a ${} prediction: +/-  US${}'.format(np.expm1(4.6), np.expm1(4.6 + acc)))
print('Error for a ${} prediction: +/-  US${}'.format(np.expm1(6.9), np.expm1(6.9 + acc)))

y_pred_test = join_predict(model1, model2, X_test, y_test[:,0], np.log(1 + y_test[:,1]))

acc = np.sqrt(mean_squared_error(y_pred_test, np.log(1 + y_test[:, 1])))
print('Final model accuracy on test set (in log):', acc)
print('Error for a $100 prediction: +/-  US$', round(np.expm1(2 + acc), 2))
print('Error for a $1000 prediction: +/-  US$', round(np.expm1(3 + acc), 2))

plt.hist(y_pred_train[:1000])