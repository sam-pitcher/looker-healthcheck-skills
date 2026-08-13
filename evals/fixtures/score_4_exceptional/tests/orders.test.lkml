test: order_id_unique {
  explore_source: orders {
    column: order_id { field: orders.order_id }
    column: count { field: orders.count }
  }
  assert: order_id_is_unique {
    expression: ${orders.count} = 1 ;;
  }
}
