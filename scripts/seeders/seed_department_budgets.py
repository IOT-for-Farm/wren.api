import sys
import pathlib
from datetime import datetime, date

ROOT_DIR = pathlib.Path(__file__).parent.parent.parent

# ADD PROJECT ROOT TO IMPORT SEARCH SCOPE
sys.path.append(str(ROOT_DIR))

from api.v1.models.department import DepartmentBudget, BudgetAdjustment
from api.v1.models.department import Department
from api.v1.models.user import User
from api.db.database import get_db_with_ctx_manager


def seed_department_budgets():
    '''Seed department budgets and budget adjustments'''
    
    with get_db_with_ctx_manager() as db:
        # Get required dependencies
        departments = Department.fetch_by_field(
            db=db,
            paginate=False
        )[1]  # Get the results, not the query
        
        users = User.fetch_by_field(
            db=db,
            paginate=False
        )[1]  # Get the results, not the query
        
        if not departments or not users:
            print("Required dependencies not found. Please run seed_departments.py and seed_users.py first.")
            return
        
        current_year = datetime.now().year
        created_budgets = []
        
        # Create budgets for each department
        for dept in departments:
            # Create annual budget
            existing_annual_budget = DepartmentBudget.fetch_one_by_field(
                db=db,
                throw_error=False,
                department_id=dept.id,
                fiscal_year=current_year,
                period_type="annual"
            )
            
            if not existing_annual_budget:
                # Set budget amount based on department type
                if "Engineering" in dept.name:
                    allocated_amount = 5000000.00  # 5M NGN
                    utilized_amount = 1200000.00
                    pending_amount = 500000.00
                elif "Sales" in dept.name:
                    allocated_amount = 3000000.00  # 3M NGN
                    utilized_amount = 800000.00
                    pending_amount = 200000.00
                elif "Customer" in dept.name:
                    allocated_amount = 2000000.00  # 2M NGN
                    utilized_amount = 600000.00
                    pending_amount = 150000.00
                elif "Installation" in dept.name:
                    allocated_amount = 4000000.00  # 4M NGN
                    utilized_amount = 1000000.00
                    pending_amount = 300000.00
                elif "Project" in dept.name:
                    allocated_amount = 1500000.00  # 1.5M NGN
                    utilized_amount = 400000.00
                    pending_amount = 100000.00
                elif "Environmental" in dept.name:
                    allocated_amount = 2500000.00  # 2.5M NGN
                    utilized_amount = 700000.00
                    pending_amount = 200000.00
                elif "Research" in dept.name:
                    allocated_amount = 3500000.00  # 3.5M NGN
                    utilized_amount = 900000.00
                    pending_amount = 250000.00
                else:
                    allocated_amount = 1000000.00  # 1M NGN default
                    utilized_amount = 250000.00
                    pending_amount = 100000.00
                
                annual_budget_data = {
                    "department_id": dept.id,
                    "fiscal_year": current_year,
                    "period_type": "annual",
                    "allocated_amount": allocated_amount,
                    "utilized_amount": utilized_amount,
                    "pending_amount": pending_amount,
                    "currency": "NGN",
                    "fiscal_period_start": date(current_year, 1, 1),
                    "fiscal_period_end": date(current_year, 12, 31)
                }
                
                new_annual_budget = DepartmentBudget.create(
                    db=db,
                    **annual_budget_data
                )
                created_budgets.append(new_annual_budget)
                print(f"Annual budget created for {dept.name}: NGN {allocated_amount:,.2f}")
                
                # Create quarterly budgets
                quarterly_amounts = [
                    (Q1 := allocated_amount * 0.25, utilized_amount * 0.3, pending_amount * 0.2),
                    (Q2 := allocated_amount * 0.25, utilized_amount * 0.25, pending_amount * 0.3),
                    (Q3 := allocated_amount * 0.25, utilized_amount * 0.25, pending_amount * 0.25),
                    (Q4 := allocated_amount * 0.25, utilized_amount * 0.2, pending_amount * 0.25)
                ]
                
                for quarter, (q_allocated, q_utilized, q_pending) in enumerate(quarterly_amounts, 1):
                    existing_quarterly_budget = DepartmentBudget.fetch_one_by_field(
                        db=db,
                        throw_error=False,
                        department_id=dept.id,
                        fiscal_year=current_year,
                        period_type="quarterly"
                    )
                    
                    if not existing_quarterly_budget:
                        start_month = (quarter - 1) * 3 + 1
                        end_month = quarter * 3
                        
                        quarterly_budget_data = {
                            "department_id": dept.id,
                            "fiscal_year": current_year,
                            "period_type": f"Q{quarter}",
                            "allocated_amount": q_allocated,
                            "utilized_amount": q_utilized,
                            "pending_amount": q_pending,
                            "currency": "NGN",
                            "fiscal_period_start": date(current_year, start_month, 1),
                            "fiscal_period_end": date(current_year, end_month, [31, 30, 30, 31][quarter-1])
                        }
                        
                        new_quarterly_budget = DepartmentBudget.create(
                            db=db,
                            **quarterly_budget_data
                        )
                        created_budgets.append(new_quarterly_budget)
                        print(f"  - Q{quarter} budget: NGN {q_allocated:,.2f}")
            else:
                print(f"Annual budget already exists for {dept.name}")
        
        # Create budget adjustments for some departments
        adjustment_depts = departments[:3]  # Create adjustments for first 3 departments
        
        for dept in adjustment_depts:
            # Get the annual budget for this department
            annual_budget = DepartmentBudget.fetch_one_by_field(
                db=db,
                throw_error=False,
                department_id=dept.id,
                fiscal_year=current_year,
                period_type="annual"
            )
            
            if annual_budget:
                # Create a budget increase request
                existing_adjustment = BudgetAdjustment.fetch_one_by_field(
                    db=db,
                    throw_error=False,
                    budget_id=annual_budget.id,
                    requester_id=users[0].id
                )
                
                if not existing_adjustment:
                    adjustment_data = {
                        "budget_id": annual_budget.id,
                        "amount": 500000.00,  # Request for 500K increase
                        "reason": "Increased project scope and additional equipment requirements",
                        "notes": f"Budget increase request for {dept.name} due to expanded project portfolio and equipment upgrades needed for Q4 operations.",
                        "status": "pending",
                        "requester_id": users[0].id,
                        "approver_id": None  # Not yet approved
                    }
                    
                    new_adjustment = BudgetAdjustment.create(
                        db=db,
                        **adjustment_data
                    )
                    print(f"Budget adjustment request created for {dept.name}: +NGN 500,000.00")
                
                # Create an approved budget adjustment for another department
                if len(departments) > 1:
                    dept2 = departments[1]
                    annual_budget2 = DepartmentBudget.fetch_one_by_field(
                        db=db,
                        throw_error=False,
                        department_id=dept2.id,
                        fiscal_year=current_year,
                        period_type="annual"
                    )
                    
                    if annual_budget2:
                        existing_adjustment2 = BudgetAdjustment.fetch_one_by_field(
                            db=db,
                            throw_error=False,
                            budget_id=annual_budget2.id,
                            status="approved"
                        )
                        
                        if not existing_adjustment2:
                            adjustment_data2 = {
                                "budget_id": annual_budget2.id,
                                "amount": -200000.00,  # Budget reduction
                                "reason": "Cost optimization and efficiency improvements",
                                "notes": f"Budget reduction for {dept2.name} due to improved operational efficiency and reduced overhead costs.",
                                "status": "approved",
                                "requester_id": users[1].id if len(users) > 1 else users[0].id,
                                "approver_id": users[0].id
                            }
                            
                            new_adjustment2 = BudgetAdjustment.create(
                                db=db,
                                **adjustment_data2
                            )
                            print(f"Approved budget adjustment for {dept2.name}: -NGN 200,000.00")
        
        print(f"Total budgets created: {len(created_budgets)}")


if __name__ == "__main__":
    seed_department_budgets()
