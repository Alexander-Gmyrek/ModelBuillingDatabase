// apiFunctions.js
const config = {
    MY_BASE_URL: "http://127.0.0.1:3000"
};

//export default config;

const BASE_URL = config.MY_BASE_URL || "http://localhost:3000";

// Helper function to make API requests
async function apiRequest(endpoint, method = "GET", body = null) {
    const options = {
        method,
        headers: {
            "Content-Type": "application/json"
        }
    };

    if (body) {
        options.body = JSON.stringify(body);
    }

    try {
        const response = await fetch(`${BASE_URL}${endpoint}`, options);
        if (!response.ok) {
            return response.json().then(err => {
                // Log the detailed JSON error message
                console.error(`HTTP error! Status: ${response.status} Error: ${err.Error}`);
                throw new Error(`HTTP error! Status: ${response.status} Error: ${err.Error}`);
            });
        }
        // else check if it is a file and auto download it
        else if (response.headers.get("content-type").includes("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")) {
            let headersObj = {};
            response.headers.forEach((value, key) => {
                headersObj[key] = value;
            });

            console.log("headers: " + JSON.stringify(headersObj) + " content-type: " + response.headers.get("content-type"));
            return response.blob().then(blob => {
                console.log("Downloading Excel file: " + response.headers.get("content-disposition").split("filename=")[1]);
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                // Get the filename from Content-Disposition and remove any surrounding quotes
                let filename = response.headers.get("content-disposition").split("filename=")[1];
                filename = decodeURIComponent(filename.replace(/^"|"$/g, '')); // Remove any leading/trailing quotes
                console.log("filename: " + filename);
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                console.log("a:" + a);
            });
        } else {
            return response.json();
        }

    } catch (error) {
        console.error("API Request Error:", error);
        throw error;
    }
}

// Employer API Functions
async function getAllEmployers() {
    return await apiRequest("/employer");
}

async function searchEmployerById(employerId) {
    return await apiRequest(`/employer/${employerId}`);
}

async function searchEmployerByName(employerName) {
    return await apiRequest(`/employer/${encodeURIComponent(employerName)}`);
}

async function searchEmployerByJson(partialJson) {
    return await apiRequest("/employer/search", "POST", partialJson);
}

async function addEmployer(employerJson) {
    return await apiRequest("/employer", "POST", employerJson);
}

async function changeEmployer(employerId, partialJson) {
    return await apiRequest(`/employer/${employerId}`, "PATCH", partialJson);
}

async function deleteEmployer(employerId) {
    return await apiRequest(`/employer/${employerId}`, "DELETE");
}

// Carrier API Functions
async function getAllCarriers() {
    return await apiRequest("/carrier");
}

async function searchCarrierById(carrierId) {
    return await apiRequest(`/carrier/${carrierId}`);
}

async function searchCarrierByName(employerID, carrierName) {
    return await apiRequest(`/carrier/${encodeURIComponent(employerID)}/${encodeURIComponent(carrierName)}`);
}

async function searchCarrierByJson(partialJson) {
    return await apiRequest("/carrier/search", "POST", partialJson);
}

async function addCarrier(carrierJson) {
    return await apiRequest("/carrier", "POST", carrierJson);
}

async function changeCarrier(carrierId, partialJson) {
    return await apiRequest(`/carrier/${carrierId}`, "PATCH", partialJson);
}

async function deleteCarrier(carrierId) {
    return await apiRequest(`/carrier/${carrierId}`, "DELETE");
}

// Tier API Functions
async function getAllTiers() {
    return await apiRequest("/tier");
}

async function searchTierById(tierId) {
    return await apiRequest(`/tier/${tierId}`);
}

async function searchTierByName(employerID, tierName) {
    return await apiRequest(`/tier/${encodeURIComponent(employerID)}/${encodeURIComponent(tierName)}`);
}

async function searchTierByJson(partialJson) {
    return await apiRequest("/tier/search", "POST", partialJson);
}

async function addTier(tierJson) {
    return await apiRequest("/tier", "POST", tierJson);
}

async function changeTier(tierId, partialJson) {
    return await apiRequest(`/tier/${tierId}`, "PATCH", partialJson);
}

async function deleteTier(tierId) {
    return await apiRequest(`/tier/${tierId}`, "DELETE");
}

// Employee API Functions
async function getAllEmployees() {
    return await apiRequest("/employee");
}

async function searchEmployeeById(employeeId) {
    return await apiRequest(`/employee/${employeeId}`);
}

async function searchEmployeeByName(employerID, employeeFullName) {
    return await apiRequest(`/employee/${encodeURIComponent(employerID)}/${encodeURIComponent(employeeFullName)}`);
}

async function searchActiveEmployees(employerID) {
    return await apiRequest(`/employee/${encodeURIComponent(employerID)}/active`);
}

async function searchEmployeeByJson(partialJson) {
    return await apiRequest("/employee/search", "POST", partialJson);
}

async function addEmployee(employeeJson) {
    return await apiRequest("/employee", "POST", employeeJson);
}

async function changeEmployee(employeeId, partialJson) {
    return await apiRequest(`/employee/${employeeId}`, "PATCH", partialJson);
}

async function deleteEmployee(employeeId) {
    return await apiRequest(`/employee/${employeeId}`, "DELETE");
}

// EmployeePlan API Functions
async function searchAllEmployeePlans() {
    return await apiRequest("/employeeplan");
}

async function searchEmployeePlanById(employeePlanId) {
    return await apiRequest(`/employeeplan/${employeePlanId}`);
}

async function searchActiveEmployeePlans(employeeID) {
    return await apiRequest(`/employeeplan/employeeID/active`);
}

async function searchEmployeePlanByJson(partialJson) {
    return await apiRequest("/employeeplan/search", "POST", partialJson);
}

async function addEmployeePlan(employeePlanJson) {
    return await apiRequest("/employeeplan", "POST", employeePlanJson);
}

async function changeEmployeePlan(employeePlanId, partialJson) {
    return await apiRequest(`/employeeplan/${employeePlanId}`, "PATCH", partialJson);
}

async function deleteEmployeePlan(employeePlanId) {
    return await apiRequest(`/employeeplan/${employeePlanId}`, "DELETE");
}

// Dependent API Functions
async function getAllDependents() {
    return await apiRequest("/dependent");
}

async function searchDependentById(dependentId) {
    return await apiRequest(`/dependent/${dependentId}`);
}

async function searchDependentByName(employerName, dependentName) {
    return await apiRequest(`/dependent/${encodeURIComponent(employerName)}/${encodeURIComponent(dependentName)}`);
}

async function searchDependentByJson(partialJson) {
    return await apiRequest("/dependent/search", "POST", partialJson);
}

async function addDependent(dependentJson) {
    return await apiRequest("/dependent", "POST", dependentJson);
}

async function changeDependent(dependentId, partialJson) {
    return await apiRequest(`/dependent/${dependentId}`, "PATCH", partialJson);
}

async function deleteDependent(dependentId) {
    return await apiRequest(`/dependent/${dependentId}`, "DELETE");
}

// Plan API Functions
async function getAllPlans() {
    return await apiRequest("/plan");
}

async function searchPlanById(planId) {
    return await apiRequest(`/plan/${planId}`);
}

async function searchPlanByName(planName) {
    return await apiRequest(`/plan/${encodeURIComponent(planName)}`);
}

async function searchPlanByJson(partialJson) {
    return await apiRequest("/plan/search", "POST", partialJson);
}

async function addPlan(planJson) {
    return await apiRequest("/plan", "POST", planJson);
}

// DO NOT USE THIS FUNCTION, IT IS NOT SAFE FOR BACKDATING AND IS ONLY FOR TESTING use modifyPlan instead
async function changePlan(planId, partialJson) {
    return await apiRequest(`/plan/${planId}`, "PATCH", partialJson);
}

// Use this function, The other one is not safe for backdating and is only for testing
async function modifyPlan(planId, partialJson) {
    return await apiRequest(`/plan/${planId}/modify`, "PATCH", partialJson);
}

// DO NOT USE THIS FUNCTION, IT IS NOT SAFE FOR BACKDATING AND IS ONLY FOR TESTING use endPlan instead
async function deletePlan(planId) {
    return await apiRequest(`/plan/${planId}`, "DELETE");
}

// Use this function, The other one is not safe for backdating and is only for testing
async function endPlan(planId) {
    return await apiRequest(`/plan/${planId}/end`, "DELETE");
}

async function searchActivePlans(EmployeerId) {
    return await apiRequest(`/plan/${EmployeerId}/active`);
}



////// General API Functions //////
async function getAllTable(tableName) {
    return await apiRequest(`/${tableName}`);
}

async function searchTableById(tableName, tableId) {
    return await apiRequest(`/${tableName}/${tableId}`);
}

async function searchTableByName(tableName, tableFullName) {
    return await apiRequest(`/${tableName}/${encodeURIComponent(tableFullName)}`);
}

async function searchTableByJson(tableName, partialJson) {
    return await apiRequest(`/${tableName}/search`, "POST", partialJson);
}

async function getFullTable(tableName, tableId) {
    return await apiRequest(`/full/${tableName}/${tableId}`);
}

async function generateReport(EmployerID, Year, Month){
    return await apiRequest(`/test/generatereport/${EmployerID}/${Year}/${Month}`);
}

// Exporting all functions for use in other files
export {
    getAllEmployers,
    searchEmployerById,
    searchEmployerByName,
    searchEmployerByJson,
    addEmployer,
    changeEmployer,
    deleteEmployer,
    getAllCarriers,
    searchCarrierById,
    searchCarrierByName,
    searchCarrierByJson,
    addCarrier,
    changeCarrier,
    deleteCarrier,
    getAllTiers,
    searchTierById,
    searchTierByName,
    searchTierByJson,
    addTier,
    changeTier,
    deleteTier,
    getAllEmployees,
    searchEmployeeById,
    searchEmployeeByName,
    searchActiveEmployees,
    searchEmployeeByJson,
    addEmployee,
    changeEmployee,
    deleteEmployee,
    searchAllEmployeePlans,
    searchEmployeePlanById,
    searchActiveEmployeePlans,
    searchEmployeePlanByJson,
    addEmployeePlan,
    changeEmployeePlan,
    deleteEmployeePlan,
    getAllDependents,
    searchDependentById,
    searchDependentByName,
    searchDependentByJson,
    addDependent,
    changeDependent,
    deleteDependent,
    getAllPlans,
    searchPlanById,
    searchPlanByName,
    searchPlanByJson,
    searchActivePlans,
    addPlan,
    changePlan,
    modifyPlan,
    deletePlan,
    endPlan,
    getAllTable,
    searchTableById,
    searchTableByName,
    searchTableByJson,
    getFullTable,
    generateReport
};
