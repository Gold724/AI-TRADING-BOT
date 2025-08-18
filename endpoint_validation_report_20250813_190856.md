# TradeBot Sentinel - Endpoint Validation Report

**Generated:** 2025-08-13T19:08:56.534197

## 📊 Summary

- **Total Endpoints:** 33
- **Valid Endpoints:** 6
- **Invalid Endpoints:** 27
- **Total Errors:** 0

## 🔄 Trade Operations

- **BUY Orders:** 2
- **SELL Orders:** 3
- **Position Close:** 1
- **Layout Requests:** 3
- **Chart Requests:** 2
- **Login Requests:** 3

## 📋 Detailed Endpoint Analysis

### Buy Orders

- ✅ **POST** `https://userapi.bulenox.projectx.com/Order`
- ✅ **POST** `https://userapi.bulenox.projectx.com/Order`

### Sell Orders

- ✅ **POST** `https://userapi.bulenox.projectx.com/Order`
- ✅ **POST** `https://userapi.bulenox.projectx.com/Order`
- ✅ **POST** `https://userapi.bulenox.projectx.com/Order`

### Position Close

- ✅ **DELETE** `https://userapi.bulenox.projectx.com/Position/close/228936/symbol/F.US.GCE`

### Layouts

- ❌ **POST** ` https://userapi.bulenox.projectx.com/Layouts `
  - ⚠️ Missing required field: accountId
  - ⚠️ Missing required field: symbolId
- ❌ **POST** `https://userapi.bulenox.projectx.com/Layouts`
  - ⚠️ Missing required field: accountId
  - ⚠️ Missing required field: symbolId
- ❌ **POST** `https://userapi.bulenox.projectx.com/Layouts`
  - ⚠️ Missing required field: accountId
  - ⚠️ Missing required field: symbolId

### Charts

- ❌ **POST** `https://userapi.bulenox.projectx.com/charts`
  - ⚠️ Missing required field: accountId
  - ⚠️ Missing required field: symbolId
- ❌ **POST** `https://userapi.bulenox.projectx.com/charts`
  - ⚠️ Missing required field: accountId
  - ⚠️ Missing required field: symbolId

### Login

- ❌ **POST** ` https://userapi.bulenox.projectx.com/Login `
  - ⚠️ Missing required field: accountId
  - ⚠️ Missing required field: symbolId
  - ⚠️ Missing authorization header
- ❌ **POST** `https://userapi.bulenox.projectx.com/Login`
  - ⚠️ Missing required field: accountId
  - ⚠️ Missing required field: symbolId
  - ⚠️ Missing authorization header
- ❌ **POST** `https://userapi.bulenox.projectx.com/Login`
  - ⚠️ Missing required field: accountId
  - ⚠️ Missing required field: symbolId
  - ⚠️ Missing authorization header

