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

async function searchCarrierByName(employerName, carrierName) {
    return await apiRequest(`/carrier/${encodeURIComponent(employerName)}/${encodeURIComponent(carrierName)}`);
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

async function searchTierByName(employerName, tierName) {
    return await apiRequest(`/tier/${encodeURIComponent(employerName)}/${encodeURIComponent(tierName)}`);
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

async function searchEmployeeByName(employerName, employeeFullName) {
    return await apiRequest(`/employee/${encodeURIComponent(employerName)}/${encodeURIComponent(employeeFullName)}`);
}

async function searchActiveEmployees(employerName) {
    return await apiRequest(`/employee/${encodeURIComponent(employerName)}/active`);
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

async function searchEmployeePlanByName(employeeFullName, planName) {
    return await apiRequest(`/employeeplan/${encodeURIComponent(employeeFullName)}/${encodeURIComponent(planName)}`);
}

async function searchActiveEmployeePlans(employeeFullName) {
    return await apiRequest(`/employeeplan/${encodeURIComponent(employeeFullName)}/active`);
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

async function changePlan(planId, partialJson) {
    return await apiRequest(`/plan/${planId}`, "PATCH", partialJson);
}

async function deletePlan(planId) {
    return await apiRequest(`/plan/${planId}`, "DELETE");
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
    searchEmployeePlanByName,
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
    addPlan,
    changePlan,
    deletePlan
};
