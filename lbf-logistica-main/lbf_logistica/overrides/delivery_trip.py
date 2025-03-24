import frappe
from datetime import datetime, timedelta

def update_shipment_from_delivery_trip(doc, method):
    for stop in doc.delivery_stops:
        shipment = frappe.get_doc("Shipment", stop.custom_shipment_id)

        shipment.append("custom_delivery_trip_th", {
            "delivery_trip_id": doc.name,
            "driver": doc.driver,
            "vehicle_number_plate": doc.vehicle,
            "est_arrival": stop.estimated_arrival,
            "departed_time": doc.departure_time
        })

        shipment.flags.ignore_validate = True
        shipment.flags.ignore_mandatory = True
        shipment.flags.ignore_validate_update_after_submit = True
        shipment.flags.ignore_permissions = True
        shipment.save()



def update_shipment_status_from_delivery_trip(doc, method):
    for stop in doc.delivery_stops:
        if stop.custom_shipment_id: 
            shipment = frappe.get_doc("Shipment", stop.custom_shipment_id)

            stop_estimated_time = datetime.strptime(stop.estimated_arrival, '%Y-%m-%d %H:%M:%S').time()

            for row in shipment.custom_delivery_trip_th:
                if isinstance(row.est_arrival, timedelta):
                    shipment_estimated_time = (datetime.min + row.est_arrival).time()
                elif isinstance(row.est_arrival, str):
                    shipment_estimated_time = datetime.strptime(row.est_arrival, '%Y-%m-%d %H:%M:%S').time()
                else:
                    continue  

                if row.delivery_trip_id == doc.name and stop_estimated_time == shipment_estimated_time:
                    row.status = stop.custom_status

                    frappe.db.set_value(
                        "Delivery Trip TH",  
                        row.name, 
                        "status",  
                        stop.custom_status  
                    )

            shipment.flags.ignore_validate = True
            shipment.flags.ignore_mandatory = True
            shipment.flags.ignore_permissions = True
            shipment.flags.ignore_validate_update_after_submit = True
            shipment.save()
            frappe.db.commit()




