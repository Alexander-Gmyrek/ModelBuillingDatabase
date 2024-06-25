CREATE DATABASE IF NOT EXISTS modelBillingDBv1;
USE modelBillingDBv1;
CREATE TABLE Employer (
    EmployerID INT AUTO_INCREMENT,
    EmployerName VARCHAR(255),
    TierStructure VARCHAR(255),
    UsesGlCode BOOLEAN,
    UsesDivision BOOLEAN,
    UsesLocation BOOLEAN,
    UsesTitle BOOLEAN,
    PerferedBillingDate DATE,
    RenewalDate DATE,
    PRIMARY KEY (EmployerID)
);

CREATE TABLE Contact (
    ContactID INT AUTO_INCREMENT,
    EmployerID INT,
    ContactName VARCHAR(255),
    PhoneNumber VARCHAR(15),
    Email VARCHAR(255),
    PRIMARY KEY (ContactID),
    FOREIGN KEY (EmployerID) REFERENCES Employer(EmployerID) ON DELETE CASCADE
);



CREATE TABLE Carrier (
    CarrierID INT AUTO_INCREMENT,
    EmployerID INT,
    CarrierName VARCHAR(255),
    PRIMARY KEY (CarrierID),
    FOREIGN KEY (EmployerID) REFERENCES Employer(EmployerID) ON DELETE CASCADE
);

CREATE TABLE Tier (
    TierID INT AUTO_INCREMENT,
    EmployerID INT,
    TierName VARCHAR(255),
    MaxAge INT,
    MinAge INT,
    PRIMARY KEY (TierID),
    FOREIGN KEY (EmployerID) REFERENCES Employer(EmployerID) ON DELETE CASCADE
);

CREATE TABLE Plan (
    PlanID INT AUTO_INCREMENT,
    EmployerID INT,
    PlanName VARCHAR(255),
    FundingAmount DECIMAL(10, 2),
    GrenzFee DECIMAL(10, 2),
    GrenzFeeC DECIMAL(10, 2),
    GrenzFeeS DECIMAL(10, 2),
    CarrierID INT,
    TierID INT,
    StartDate DATE,
    EndDate DATE,
    PRIMARY KEY (PlanID),
    FOREIGN KEY (EmployerID) REFERENCES Employer(EmployerID) ON DELETE CASCADE,
    FOREIGN KEY (TierID) REFERENCES Tier(TierID) ON DELETE CASCADE,
    FOREIGN KEY (CarrierID) REFERENCES Carrier(CarrierID) ON DELETE CASCADE
);

CREATE TABLE Employee (
    EmployeeID INT AUTO_INCREMENT,
    EmployerID INT,
    EmployeeFullName VARCHAR(255),
    EmployeeFirstName VARCHAR(255),
    EmployeeLastName VARCHAR(255),
    JoinDate DATE,
    TermDate DATE,
    JoinInformDate DATE,
    TermEndDate DATE,
    DOB DATE,
    CobraStatus BOOLEAN,
    Notes TEXT,
    GlCode VARCHAR(255),
    Division VARCHAR(255),
    Location VARCHAR(255),
    Title VARCHAR(255),
    PRIMARY KEY (EmployeeID),
    FOREIGN KEY (EmployerID) REFERENCES Employer(EmployerID) ON DELETE CASCADE
);

CREATE TABLE EmployeePlan (
    EmployeePlanID INT AUTO_INCREMENT,
    EmployeeID INT,
    PlanID INT,
    StartDate DATE,
    InformStartDate DATE,
    EndDate DATE,
    InformEndDate DATE,
    PRIMARY KEY (EmployeePlanID),
    FOREIGN KEY (EmployeeID) REFERENCES Employee(EmployeeID) ON DELETE CASCADE,
    FOREIGN KEY (PlanID) REFERENCES Plan(PlanID) ON DELETE CASCADE
);

CREATE TABLE Dependent (
    DependentID INT AUTO_INCREMENT,
    EmployeeID INT,
    DOB DATE,
    Relationship VARCHAR(255),
    DependentName VARCHAR(255),
    StartDate DATE,
    InformStartDate DATE,
    EndDate DATE,
    InformEndDate DATE,
    PRIMARY KEY (DependentID),
    FOREIGN KEY (EmployeeID) REFERENCES Employee(EmployeeID) ON DELETE CASCADE
);
