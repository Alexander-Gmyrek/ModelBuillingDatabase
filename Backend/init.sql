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
    FOREIGN KEY (EmployerID) REFERENCES Employer(EmployerID),
    CONSTRAINT fk_Contact_Employer FOREIGN KEY (EmployerID)
        REFERENCES Employer(EmployerID)
        ON DELETE CASCADE
);

CREATE TABLE Month (
    MonthID INT AUTO_INCREMENT,
    MonthName VARCHAR(255),
    PRIMARY KEY (MonthID)
);

CREATE TABLE EmployerFunding (
    EmployerFundingID INT AUTO_INCREMENT,
    MonthID INT,
    EmployerID INT,
    EmployerFunding DECIMAL(10, 2),
    Claims DECIMAL(10, 2),
    Total DECIMAL(10, 2),
    PRIMARY KEY (EmployerFundingID),
    FOREIGN KEY (MonthID) REFERENCES Month(MonthID),
    FOREIGN KEY (EmployerID) REFERENCES Employer(EmployerID),
    CONSTRAINT fk_EmployerFunding_Employer FOREIGN KEY (EmployerID)
        REFERENCES Employer(EmployerID)
        ON DELETE CASCADE
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
    PRIMARY KEY (PlanID),
    FOREIGN KEY (EmployerID) REFERENCES Employer(EmployerID),
    CONSTRAINT fk_Plan_Employer FOREIGN KEY (EmployerID)
        REFERENCES Employer(EmployerID)
        ON DELETE CASCADE,
    FOREIGN KEY (TierID) REFERENCES Tier(TierID)
    CONSTRAINT fk_Plan_Tier FOREIGN KEY (TierID)
        REFERENCES Tier(TierID)
        ON DELETE CASCADE,
    FOREIGN KEY (CarrierID) REFERENCES Carrier(CarrierID)
    CONSTRAINT fk_Plan_Carrier FOREIGN KEY (CarrierID)
        REFERENCES Carrier(CarrierID)
        ON DELETE CASCADE
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
    GL VARCHAR(255),
    Division VARCHAR(255),
    Location VARCHAR(255),
    Title VARCHAR(255),
    PRIMARY KEY (EmployeeID),
    FOREIGN KEY (EmployerID) REFERENCES Employer(EmployerID),
    CONSTRAINT fk_Employee_Employer FOREIGN KEY (EmployerID)
        REFERENCES Employer(EmployerID)
        ON DELETE CASCADE
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
    FOREIGN KEY (EmployeeID) REFERENCES Employee(EmployeeID),
    FOREIGN KEY (PlanID) REFERENCES Plan(PlanID),
    CONSTRAINT fk_EmployeePlan_Employee FOREIGN KEY (EmployeeID)
        REFERENCES Employee(EmployeeID)
        ON DELETE CASCADE,
    CONSTRAINT fk_EmployeePlan_Plan FOREIGN KEY (PlanID)
        REFERENCES Plan(PlanID)
        ON DELETE CASCADE
);

CREATE TABLE Dependent (
    DependentID INT AUTO_INCREMENT,
    EmployeeID INT,
    DOB DATE,
    RelationshipStatus VARCHAR(255),
    Name VARCHAR(255),
    StartDate DATE,
    InformStartDate DATE,
    EndDate DATE,
    InformEndDate DATE,
    PRIMARY KEY (DependentID),
    FOREIGN KEY (EmployeeID) REFERENCES Employee(EmployeeID),
    CONSTRAINT fk_Dependent_Employee FOREIGN KEY (EmployeeID)
        REFERENCES Employee(EmployeeID)
        ON DELETE CASCADE
);

-- Creating the Carrier table
CREATE TABLE Carrier (
    CarrierID INT AUTO_INCREMENT,
    EmployerID INT,
    CarrierName VARCHAR(255),
    PRIMARY KEY (CarrierID),
    FOREIGN KEY (EmployerID) REFERENCES Employer(EmployerID),
    CONSTRAINT fk_Carrier_Employer FOREIGN KEY (EmployerID)
        REFERENCES Employer(EmployerID)
        ON DELETE CASCADE
);

-- Creating the Tier table
CREATE TABLE Tier (
    TierID INT AUTO_INCREMENT,
    EmployerID INT,
    Name VARCHAR(255),
    PRIMARY KEY (TierID),
    MaxAge INT,
    MinAge INT,
    FOREIGN KEY (EmployerID) REFERENCES Employer(EmployerID),
    CONSTRAINT fk_Tier_Employer FOREIGN KEY (EmployerID)
        REFERENCES Employer(EmployerID)
        ON DELETE CASCADE
);