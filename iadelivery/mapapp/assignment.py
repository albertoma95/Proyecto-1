from datetime import datetime, timedelta
from .routing_alg import dijkstra

def can_assign_order_to_truck(order, truck, graph, origin, speed):
    order_id, destination, expiration_date, total_quantity, order_ready, name, total_cost = order
    if truck['total_quantity'] + total_quantity > truck['capacity']:
        return False

    expiration_date_obj = datetime.strptime(str(expiration_date), '%Y-%m-%d')
    current_date = truck['current_date']
    distance, _ = dijkstra(graph, origin, destination)
    if distance == float('inf'):
        return False
    time_to_destination = timedelta(hours=distance / speed)
    arrival_date = current_date + time_to_destination
    if arrival_date > expiration_date_obj:
        return False

    return True

def assign_orders_to_trucks(graph, origin, orders, capacity, speed):
    unassigned_orders = list(orders)
    trucks = []
    unassigned_orders.sort(key=lambda x: x[2])  # x[2] es expiration_date

    while unassigned_orders:
        truck = {
            'orders': [],
            'total_quantity': 0,
            'capacity': capacity,
            'current_date': datetime.now()
        }

        assigned_this_round = True
        while assigned_this_round and unassigned_orders:
            assigned_this_round = False
            for order in unassigned_orders:
                if truck['orders']:
                    max_order_ready = max(datetime.strptime(str(o[4]), '%Y-%m-%d') for o in truck['orders'])
                else:
                    max_order_ready = datetime.strptime(str(order[4]), '%Y-%m-%d')

                if max_order_ready > truck['current_date']:
                    truck['current_date'] = max_order_ready

                if can_assign_order_to_truck(order, truck, graph, origin, speed):
                    truck['orders'].append(order)
                    truck['total_quantity'] += order[3]
                    unassigned_orders.remove(order)
                    assigned_this_round = True
                    break

        if truck['orders']:
            trucks.append(truck)

    return trucks
