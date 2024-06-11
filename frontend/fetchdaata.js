// apiFunctions.js

const BASE_URL = "http://localhost:5000";

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
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error("API Request Error:", error);
        throw error;
    }
}

// Employer API Functions
async function getAllEmployers() {
    return await apiRequest("/employer");
}

async function getEmployerByName(employerName) {
    return await apiRequest(`/employer/${encodeURIComponent(employerName)}`);
}

async function searchEmployerByJson(partialJson) {
    return await apiRequest("/employer/search", "GET", partialJson);
}

async function addEmployer(employerJson) {
    return await apiRequest("/employer", "POST", employerJson);
}

async function changeEmployer(employerName, partialJson) {
    return await apiRequest(`/employer/${encodeURIComponent(employerName)}`, "PATCH", partialJson);
}

async function deleteEmployer(employerName) {
    return await apiRequest(`/employer/${encodeURIComponent(employerName)}`, "DELETE");
}

// Carrier API Functions
async function getAllCarriers() {
    return await apiRequest("/carrier");
}

async function getCarrierByName(employerName, carrierName) {
    return await apiRequest(`/carrier/${encodeURIComponent(employerName)}/${encodeURIComponent(carrierName)}`);
}

async function addCarrier(carrierJson) {
    return await apiRequest("/carrier", "POST", carrierJson);
}

async function changeCarrier(employerName, carrierName, partialJson) {
    return await apiRequest(`/carrier/${encodeURIComponent(employerName)}/${encodeURIComponent(carrierName)}`, "PATCH", partialJson);
}

async function deleteCarrier(employerName, carrierName) {
    return await apiRequest(`/carrier/${encodeURIComponent(employerName)}/${encodeURIComponent(carrierName)}`, "DELETE");
}

// Tier API Functions
async function getAllTiers() {
    return await apiRequest("/tier");
}

async function getTierByName(employerName, tierName) {
    return await apiRequest(`/tier/${encodeURIComponent(employerName)}/${encodeURIComponent(tierName)}`);
}

async function addTier(tierJson) {
    return await apiRequest("/tier", "POST", tierJson);
}

async function changeTier(employerName, tierName, partialJson) {
    return await apiRequest(`/tier/${encodeURIComponent(employerName)}/${encodeURIComponent(tierName)}`, "PATCH", partialJson);
}

async function deleteTier(employerName, tierName) {
    return await apiRequest(`/tier/${encodeURIComponent(employerName)}/${encodeURIComponent(tierName)}`, "DELETE");
}

// Employee API Functions
async function getAllEmployees() {
    return await apiRequest("/employee");
}

async function getEmployeeByName(employerName, employeeFullName) {
    return await apiRequest(`/employee/${encodeURIComponent(employerName)}/${encodeURIComponent(employeeFullName)}`);
}

async function getActiveEmployees(employerName) {
    return await apiRequest(`/employee/${encodeURIComponent(employerName)}/active`);
}

async function addEmployee(employeeJson) {
    return await apiRequest("/employee", "POST", employeeJson);
}

async function changeEmployee(employerName, employeeFullName, partialJson) {
    return await apiRequest(`/employee/${encodeURIComponent(employerName)}/${encodeURIComponent(employeeFullName)}`, "PATCH", partialJson);
}

async function deleteEmployee(employerName, employeeFullName) {
    return await apiRequest(`/employee/${encodeURIComponent(employerName)}/${encodeURIComponent(employeeFullName)}`, "DELETE");
}

// EmployeePlan API Functions
async function getAllEmployeePlans() {
    return await apiRequest("/employeeplan");
}

async function getEmployeePlanByName(employeeFullName, planName) {
    return await apiRequest(`/employeeplan/${encodeURIComponent(employeeFullName)}/${encodeURIComponent(planName)}`);
}

async function getActiveEmployeePlans(employeeFullName) {
    return await apiRequest(`/employeeplan/${encodeURIComponent(employeeFullName)}/active`);
}

async function addEmployeePlan(employeePlanJson) {
    return await apiRequest("/employeeplan", "POST", employeePlanJson);
}

async function changeEmployeePlan(employeeFullName, planName, partialJson) {
    return await apiRequest(`/employeeplan/${encodeURIComponent(employeeFullName)}/${encodeURIComponent(planName)}`, "PATCH", partialJson);
}

async function deleteEmployeePlan(employeeFullName, planName) {
    return await apiRequest(`/employeeplan/${encodeURIComponent(employeeFullName)}/${encodeURIComponent(planName)}`, "DELETE");
}

// Dependent API Functions
async function getAllDependents() {
    return await apiRequest("/dependent");
}

async function getDependentByName(employerName, dependentName) {
    return await apiRequest(`/dependent/${encodeURIComponent(employerName)}/${encodeURIComponent(dependentName)}`);
}

async function addDependent(dependentJson) {
    return await apiRequest("/dependent", "POST", dependentJson);
}

async function changeDependent(employerName, dependentName, partialJson) {
    return await apiRequest(`/dependent/${encodeURIComponent(employerName)}/${encodeURIComponent(dependentName)}`, "PATCH", partialJson);
}

async function deleteDependent(employerName, dependentName) {
    return await apiRequest(`/dependent/${encodeURIComponent(employerName)}/${encodeURIComponent(dependentName)}`, "DELETE");
}

// Plan API Functions
async function getAllPlans() {
    return await apiRequest("/plan");
}

async function getPlanByName(planName) {
    return await apiRequest(`/plan/${encodeURIComponent(planName)}`);
}

async function addPlan(planJson) {
    return await apiRequest("/plan", "POST", planJson);
}

async function changePlan(planName, partialJson) {
    return await apiRequest(`/plan/${encodeURIComponent(planName)}`, "PATCH", partialJson);
}

async function deletePlan(planName) {
    return await apiRequest(`/plan/${encodeURIComponent(planName)}`, "DELETE");
}

// Exporting all functions for use in other files
export {
    getAllEmployers,
    getEmployerByName,
    searchEmployerByJson,
    addEmployer,
    changeEmployer,
    deleteEmployer,
    getAllCarriers,
    getCarrierByName,
    addCarrier,
    changeCarrier,
    deleteCarrier,
    getAllTiers,
    getTierByName,
    addTier,
    changeTier,
    deleteTier,
    getAllEmployees,
    getEmployeeByName,
    getActiveEmployees,
    addEmployee,
    changeEmployee,
    deleteEmployee,
    getAllEmployeePlans,
    getEmployeePlanByName,
    getActiveEmployeePlans,
    addEmployeePlan,
    changeEmployeePlan,
    deleteEmployeePlan,
    getAllDependents,
    getDependentByName,
    addDependent,
    changeDependent,
    deleteDependent,
    getAllPlans,
    getPlanByName,
    addPlan,
    changePlan,
    deletePlan
};
