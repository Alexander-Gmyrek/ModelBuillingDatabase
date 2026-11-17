function renameSetupCarrier(oldName, newName, carriers, tiers, data) {
    const stored = localStorage.getItem('companyData');
    if (!stored) throw new Error('Company setup was not found. Return to New Company.');
    const company = JSON.parse(stored);
    if (company.EmployerID) throw new Error('This company is already saved. Use Edit Plan to rename its carriers.');
    for (const employee of company.Employees || []) {
        if (employee.Carrier === oldName) employee.Carrier = newName;
    }
    for (const carrier of company.Carriers || []) {
        if (carrier.CarrierName === oldName) carrier.CarrierName = newName;
    }
    for (const plan of company.Plans || []) {
        if (plan.CarrierName === oldName) plan.CarrierName = newName;
    }
    const renamedData = Object.create(null);
    for (const [name, amounts] of Object.entries(data)) {
        renamedData[name === oldName ? newName : name] = amounts;
    }
    company.PlanSetupDraft = {
        Carriers: carriers.map(carrier => ({ ...carrier, CarrierName: carrier.CarrierName === oldName ? newName : carrier.CarrierName })),
        Tiers: tiers, Data: renamedData
    };
    localStorage.setItem('companyData', JSON.stringify(company));
}

function showEmployeeImportPreview(employees, validation = {}) {
    return new Promise(resolve => {
        const dialog = document.createElement('dialog');
        dialog.className = 'import-preview';
        const heading = document.createElement('h2');
        heading.textContent = 'Review employee import';
        dialog.appendChild(heading);
        const starts = employees.map(employee => employee.StartDate).filter(Boolean).sort();
        const summary = document.createElement('p');
        const carriers = [...new Set(employees.map(employee => employee.Carrier || '(missing)'))];
        const tiers = [...new Set(employees.map(employee => employee.Tier || '(missing)'))];
        summary.textContent = `${employees.length} employees. ${employees.reduce((sum, employee) => sum + employee.Dependents.length, 0)} dependents. Earliest start ${starts[0] || '(missing)'}. Carriers: ${carriers.join(', ')}. Tiers: ${tiers.join(', ')}.`;
        dialog.appendChild(summary);
        const messages = document.createElement('ul');
        const warnings = [...(validation.Warnings || [])];
        const missingDOB = employees.filter(employee => !employee.DOB).length;
        if (missingDOB) warnings.push(`${missingDOB} employees have no birth date. Age-banded plans require birth dates.`);
        const sameDates = employees.filter(employee => employee.StartDate === employee.InformStartDate).length;
        if (sameDates) warnings.push(`${sameDates} informed dates match coverage starts. Check these dates for late additions.`);
        if (validation.NewCount != null) warnings.push(`${validation.NewCount} new employees; ${validation.SkippedCount} existing employees skipped.`);
        for (const message of [...(validation.Errors || []), ...warnings]) {
            const item = document.createElement('li');
            item.textContent = message;
            messages.appendChild(item);
        }
        dialog.appendChild(messages);
        const wrapper = document.createElement('div');
        wrapper.className = 'import-preview-table';
        const table = document.createElement('table');
        const fields = ['EmployeeFullName', 'Carrier', 'Tier', 'StartDate', 'InformStartDate', 'DOB'];
        const head = table.createTHead().insertRow();
        for (const label of ['Employee', 'Carrier', 'Tier', 'Coverage start', 'Informed start', 'Birth date']) {
            const cell = document.createElement('th');
            cell.textContent = label;
            head.appendChild(cell);
        }
        const body = table.createTBody();
        for (const employee of employees) {
            const row = body.insertRow();
            for (const field of fields) row.insertCell().textContent = employee[field] || '(blank)';
        }
        wrapper.appendChild(table);
        dialog.appendChild(wrapper);
        const actions = document.createElement('div');
        actions.className = 'actions';
        const cancel = document.createElement('button');
        cancel.type = 'button';
        cancel.className = 'secondary';
        cancel.textContent = 'Back';
        const proceed = document.createElement('button');
        proceed.type = 'button';
        proceed.textContent = 'Continue';
        proceed.disabled = Boolean(validation.Errors?.length);
        cancel.addEventListener('click', () => dialog.close('cancel'));
        proceed.addEventListener('click', () => dialog.close('continue'));
        actions.append(cancel, proceed);
        dialog.appendChild(actions);
        dialog.addEventListener('close', () => {
            const accepted = dialog.returnValue === 'continue';
            dialog.remove();
            resolve(accepted);
        }, { once: true });
        document.body.appendChild(dialog);
        dialog.showModal();
    });
}

            async function readEmployeeSpreadsheet(file) {
                        const data = await file.arrayBuffer();
                        const workbook = XLSX.read(data, { type: 'array' });

                        // Assuming the first sheet contains the employee data
                        const sheetName = workbook.SheetNames[0];
                        const worksheet = workbook.Sheets[sheetName];
                        const jsonData = XLSX.utils.sheet_to_json(worksheet).map(normalizeImportRow);
                        if (!jsonData.length) {
                            throw new Error('Put employee rows on the first worksheet.');
                        }

                        // Define the structure of the employee and dependent objects with default values
                        const employeeTemplate = {
                            //"EmployeeID": null,
                            //"EmployerID": 1, // Assuming a fixed EmployerID for demo
                            "EmployeeFullName": null,
                            "EmployeeFirstName": null,
                            "EmployeeLastName": null,
                            "StartDate": null,
                            "EndDate": null,
                            "InformStartDate": null,
                            //"InformEndDate": null,
                            "DOB": null,
                            "CobraStatus": null,
                            "Notes": null,
                            "GlCode": null,
                            "Division": null,
                            "Location": null,
                            "Title": null,
                            "Dependents": [],
                            "Carrier": null,
                            "Tier": null,
                        };

                        const dependentTemplate = {
                            //"DependentID": null,
                            //"EmployeeID": null,
                            "DependentName": null,
                            "Relationship": null,
                            "DOB": null,
                            "StartDate": null,
                            //"InformStartDate": null,
                            "EndDate": null,
                            "InformEndDate": null
                        };

                        // Arrays to hold employees and dependents
                        const employees = [];

                        // This should be unnecessary but it just checks if all the employees have the same name
                        // If they do, it will be used as the employee name
                        // If not, the first and last name will be used
                        let checkIfTheyAcidentalyPutTheEmployeeFullNameAsTheCompanyName = true;
                        let employeeName = jsonData[0]['Employee Name'];
                        jsonData.forEach((row, index) => {
                            if (row['Employee Name'] !== employeeName) {
                                employeeName = null;
                                checkIfTheyAcidentalyPutTheEmployeeFullNameAsTheCompanyName = false;

                            }
                        });
                        if (checkIfTheyAcidentalyPutTheEmployeeFullNameAsTheCompanyName) {
                            alert('Employee Name is the same for all employees. Using it as the employee name');
                        }
                        
                        // Convert the Excel data to the employee objects
                        jsonData.forEach((row, index) => {
                            const employee = {
                                ...employeeTemplate,
                                Dependents: [], // Ensure each employee has a unique Dependents array
                            };

                            // Split Employee Name into first and last names
                            employee.EmployeeLastName = row['Last Name'] || null;
                            employee.EmployeeFirstName = row['First Name'] || null;
                            //prioritize employee firstname lastname over full name
                            if (row['Employee Name']) {
                                employee.EmployeeFullName = row['Employee Name'];
                            }else if (employee.EmployeeFirstName === null || employee.EmployeeLastName === null){
                                throw new Error(`Row ${row.__rowNum__ + 1}: Enter Employee Name or both First Name and Last Name.`);
                            }
                            /* check if this works- Jagger
                            //probably want to make this the main if statement
                            if (employee.EmployeeFirstName === null || employee.EmployeeLastName === null){
                                throw new Error('Employee must have a Name');
                            }
                            else if(row['Employee Name']!=employee.EmployeeFirstName + " " + employee.EmployeeLastName){
                                employee.EmployeeFullName = employee.EmployeeFirstName + " " + employee.EmployeeLastName;
                            }
                            else if (row['Employee Name'].includes(",")) {
                                const nameParts = row['Employee Name'].split(",");
                                employee.EmployeeLastName = nameParts[0].trim(); // Get the part before the comma
                                employee.EmployeeFirstName = nameParts[1].trim(); // Get the part after the comma
                                employee.EmployeeFullName = employee.EmployeeFirstName + " " + employee.EmployeeLastName;
                            }else{
                                employee.EmployeeFullName = row['Employee Name'];
                            }
                            */
                            else{
                                employee.EmployeeFullName = employee.EmployeeFirstName + " " + employee.EmployeeLastName;
                            }
                            

                            // Map other fields from the row if available
                            employee.Notes = row['Notes'] || null;
                            const rowDate = field => formatDate(row[field], row.__rowNum__ + 1, field, workbook.Workbook?.WBProps?.date1904);
                            employee.DOB = rowDate('DOB');
                            employee.Tier = row['Tier'] || null;
                            //employee.Plan = row['Plan'] || null;
                            employee.Carrier = row['Carrier'] || null;
                            employee.GlCode = row['GL'] || null;
                            employee.Division = row['Division'] || null;
                            employee.Location = row['Location'] || null;
                            employee.CobraStatus = parseCobraStatus(row['cobra'], row.__rowNum__ + 1);
                            employee.Title= row['Title'] || null

                            employee.StartDate = rowDate('Start Date');
                            employee.InformStartDate = rowDate('Inform Start Date') || employee.StartDate;
                            if (!employee.StartDate) throw new Error(`Row ${row.__rowNum__ + 1}: Start Date is required.`);

                            // check if is dependent
                            if (row['Dependent Name'] || row['Relationship'] || row['Dependent DOB'] || row['Dependent']) {
                                if (!row['Dependent Name'] || !row['Relationship'] || !row['Dependent DOB']) {
                                    throw new Error(`Row ${row.__rowNum__ + 1}: Dependent Name, Relationship, and Dependent DOB are required for a dependent.`);
                                }
                                const dependent = { ...dependentTemplate };
                                //console.log("Dependent on row: " + index);
                                //dependent.DependentID = dependentIDCounter++;
                                //dependent.EmployeeID = employee.EmployeeID;
                                dependent.DependentName = row['Dependent Name'];
                                dependent.Relationship = row['Relationship'];
                                dependent.DOB = rowDate('Dependent DOB');
                                dependent.StartDate = rowDate('Dependent Start Date');
                                dependent.InformStartDate = rowDate('Dependent Inform Start Date');
                                dependent.Notes = row['Notes'] || null;


                                //get the dependent's employee
                                const dependentsEmployee = findDependentsEmployee(employee, employees);

                                if(!dependentsEmployee || dependentsEmployee.length === 0){
                                    throw new Error(`Row ${row.__rowNum__ + 1}: Repeat the employee details from the employee row above this dependent.`);
                                }
                                

                                const empIndex = employees.findIndex(e => dependentsEmployee[dependentsEmployee.length-1] === e);
                                //console.log("empIndex: " + empIndex);

                                employees[empIndex].Dependents.push(dependent);
                                //console.log(`Dependent added:`, dependent, `to employee:`, employees[empIndex]);
                            }else{
                                // Add the employee to the array
                                //console.log(`Employee added:`, employee);
                                employees.push(employee);
                            }
                        });

                        return employees;
            }

        function parseCobraStatus(value, rowNumber) {
            const status = String(value ?? '').trim().toLowerCase();
            if (!status) return false;
            if (['yes', 'true', '1'].includes(status)) return true;
            if (['no', 'false', '0'].includes(status)) return false;
            throw new Error(`Row ${rowNumber}: Enter Yes or No in the cobra column.`);
        }

        function normalizeImportRow(source) {
            const fields = ['Employee Name', 'First Name', 'Last Name', 'DOB', 'Tier', 'Carrier', 'GL', 'Division', 'Location', 'cobra', 'Title', 'Notes', 'Start Date', 'Inform Start Date', 'Dependent', 'Dependent Name', 'Relationship', 'Dependent DOB', 'Dependent Start Date', 'Dependent Inform Start Date'];
            const key = value => String(value).trim().toLowerCase().replace(/\s+/g, '');
            const aliases = Object.fromEntries(fields.map(field => [key(field), field]));
            aliases.glcode = 'GL';
            aliases.cobrastatus = 'cobra';
            const row = { __rowNum__: source.__rowNum__ };
            for (const [header, value] of Object.entries(source)) {
                const field = aliases[key(header)];
                if (!field) continue;
                if (Object.hasOwn(row, field)) throw new Error(`Row ${source.__rowNum__ + 1}: Duplicate column ${field}.`);
                row[field] = typeof value === 'string' ? value.trim() : value;
            }
            return row;
        }

        function formatDate(value, rowNumber, field = 'Date', date1904 = false) {
            if (value == null || value === '') return null;
            let parts;
            if (typeof value === 'number' && Number.isFinite(value) && Number.isInteger(value)) {
                const parsed = XLSX.SSF.parse_date_code(value, { date1904: !!date1904 });
                if (parsed) parts = [parsed.y, parsed.m, parsed.d];
            } else if (typeof value === 'string') {
                let match = value.trim().match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);
                if (match) parts = match.slice(1).map(Number);
                else {
                    match = value.trim().match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
                    if (match) parts = [Number(match[3]), Number(match[1]), Number(match[2])];
                }
            }
            if (parts) {
                const [year, month, day] = parts;
                const date = new Date(Date.UTC(year, month - 1, day));
                if (year >= 1900 && year <= 2400 && date.getUTCFullYear() === year && date.getUTCMonth() === month - 1 && date.getUTCDate() === day) {
                    return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
                }
            }
            throw new Error(`Row ${rowNumber}: ${field} must be a valid date (YYYY-MM-DD, M/D/YYYY, or an Excel date), from 1900 to 2400.`);
        }

        function monthToDate(value) {
            return /^(?:19\d{2}|2[0-3]\d{2}|2400)-(?:0[1-9]|1[0-2])$/.test(value || '') ? `${value}-01` : '';
        }

        function findDependentsEmployee(employee, employees) {
            // Look for the employee that matches all values except the dependents and notes
            return employees.filter(e => {
                for (const key in employee) {
                    if (key === 'Dependents' || key === 'Notes') continue;
                    if (employee[key] !== e[key]) return false;
                }
                return true;
            });
        }
