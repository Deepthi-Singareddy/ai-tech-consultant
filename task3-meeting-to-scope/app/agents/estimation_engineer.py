from typing import List
from app.schemas.models import RequirementItem, WBSTask

class EstimationEngineerAgent:
    """
    Constructs an engineering Work Breakdown Structure (WBS) with 3-point PERT estimation:
    Expected Hours = (Optimistic + 4*Likely + Pessimistic) / 6
    """

    def generate_wbs(self, requirements: List[RequirementItem]) -> List[WBSTask]:
        tasks: List[WBSTask] = []
        counter = 1

        for req in requirements:
            req_id = req.req_id

            if req.feasibility == "BUILTIN_SETTING":
                # Low effort: Admin Configuration and Verification
                t_id = f"TSK-{counter:03d}"
                counter += 1
                o = 1.0
                m = 2.0
                p = 3.5
                pert = round((o + 4 * m + p) / 6.0, 2)
                tasks.append(WBSTask(
                    task_id=t_id,
                    req_id=req_id,
                    name=f"Admin Configuration: {req.description}",
                    category="Configuration",
                    optimistic_hours=o,
                    likely_hours=m,
                    pessimistic_hours=p,
                    expected_hours_pert=pert,
                    notes=f"Native BD setting. Verification & data validation."
                ))

            elif req.feasibility == "PARTIAL_SETTING":
                # Configuration + Webhook mapping
                t_id1 = f"TSK-{counter:03d}"
                counter += 1
                o1, m1, p1 = 2.0, 3.5, 6.0
                pert1 = round((o1 + 4 * m1 + p1) / 6.0, 2)
                tasks.append(WBSTask(
                    task_id=t_id1,
                    req_id=req_id,
                    name=f"Webhook Configuration & Endpoint Setup",
                    category="Configuration",
                    optimistic_hours=o1,
                    likely_hours=m1,
                    pessimistic_hours=p1,
                    expected_hours_pert=pert1,
                    notes="Configuring Developer Tools webhooks."
                ))

                t_id2 = f"TSK-{counter:03d}"
                counter += 1
                o2, m2, p2 = 3.0, 5.0, 8.0
                pert2 = round((o2 + 4 * m2 + p2) / 6.0, 2)
                tasks.append(WBSTask(
                    task_id=t_id2,
                    req_id=req_id,
                    name=f"Integration: Zapier/QuickBooks payload mapping",
                    category="Backend",
                    optimistic_hours=o2,
                    likely_hours=m2,
                    pessimistic_hours=p2,
                    expected_hours_pert=pert2,
                    notes="Testing data sync and exception handling."
                ))

            elif req.feasibility == "CUSTOM_DEVELOPMENT":
                # Frontend + Backend + Testing
                t_id1 = f"TSK-{counter:03d}"
                counter += 1
                o1, m1, p1 = 4.0, 7.0, 12.0
                pert1 = round((o1 + 4 * m1 + p1) / 6.0, 2)
                tasks.append(WBSTask(
                    task_id=t_id1,
                    req_id=req_id,
                    name=f"UI/UX Implementation: {req.description}",
                    category="Frontend",
                    optimistic_hours=o1,
                    likely_hours=m1,
                    pessimistic_hours=p1,
                    expected_hours_pert=pert1,
                    notes="Custom HTML, CSS, and responsive styling."
                ))

                t_id2 = f"TSK-{counter:03d}"
                counter += 1
                o2, m2, p2 = 4.0, 8.0, 14.0
                pert2 = round((o2 + 4 * m2 + p2) / 6.0, 2)
                tasks.append(WBSTask(
                    task_id=t_id2,
                    req_id=req_id,
                    name=f"Custom Logic & API Integration",
                    category="Backend",
                    optimistic_hours=o2,
                    likely_hours=m2,
                    pessimistic_hours=p2,
                    expected_hours_pert=pert2,
                    notes="Custom JavaScript / PHP widget integration."
                ))

        # Always add QA & End-to-End Testing Task
        t_id_qa = f"TSK-{counter:03d}"
        o_qa, m_qa, p_qa = 2.0, 4.0, 6.0
        pert_qa = round((o_qa + 4 * m_qa + p_qa) / 6.0, 2)
        tasks.append(WBSTask(
            task_id=t_id_qa,
            name="End-to-End Quality Assurance & Acceptance Testing",
            category="QA / Acceptance",
            optimistic_hours=o_qa,
            likely_hours=m_qa,
            pessimistic_hours=p_qa,
            expected_hours_pert=pert_qa,
            notes="Cross-device testing, payment sandbox checkout, regression test."
        ))

        return tasks

estimation_engineer = EstimationEngineerAgent()
