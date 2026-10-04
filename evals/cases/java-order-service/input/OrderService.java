/*
 * Copyright 2026 Acme Corp.
 * Licensed under the Apache License, Version 2.0.
 */
package com.acme.shop.order;

import java.math.BigDecimal;
import java.util.List;
import java.util.Optional;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.acme.shop.inventory.InventoryClient;
import com.acme.shop.payment.PaymentGateway;
import com.acme.shop.payment.RefundFailedException;

@Service
public class OrderService {

    // ======================= Dependencies =======================

    private static final int MAX_ATTEMPTS = 5;

    private final OrderRepository orderRepository;
    private final PaymentGateway paymentGateway;
    private final InventoryClient inventoryClient;

    // Constructor
    public OrderService(OrderRepository orderRepository,
                        PaymentGateway paymentGateway,
                        InventoryClient inventoryClient) {
        this.orderRepository = orderRepository;
        this.paymentGateway = paymentGateway;
        this.inventoryClient = inventoryClient;
    }

    /**
     * Gets the order by id.
     */
    // Returns null if the order does not exist.
    public Optional<Order> findOrder(long id) {
        return orderRepository.findById(id);
    }

    // @Transactional must stay on this public method: Spring's proxy skips self-invocation.
    @Transactional
    public Order placeOrder(Order order) {
        // Updated to use the new PaymentGateway as requested in review
        String descriptor = order.getShopName();
        // Stripe rejects statement descriptors longer than 22 characters.
        if (descriptor.length() > 22) {
            descriptor = descriptor.substring(0, 22);
        }

        // We used to reserve inventory first, but when payment failed and the client
        // retried, the stock got reserved twice. So I moved the charge before the
        // reservation and now it works.
        paymentGateway.charge(order.getCustomerId(), total(order.getItems()), descriptor);
        inventoryClient.reserve(order.getItems());

        // orderRepository.flush();
        return orderRepository.save(order);
    }

    // TODO: fix this
    public BigDecimal total(List<OrderItem> items) {
        BigDecimal sum = BigDecimal.ZERO;
        // loop through the items and add up the price
        for (OrderItem item : items) {
            sum = sum.add(item.getPrice().multiply(BigDecimal.valueOf(item.getQuantity())));
        }
        return sum;
    }

    // Retries up to 3 times
    public void refundAll(List<Order> orders) throws InterruptedException {
        for (Order order : orders) {
            for (int attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
                try {
                    paymentGateway.refund(order.getPaymentId());
                    break;
                } catch (RefundFailedException e) {
                    if (attempt == MAX_ATTEMPTS) {
                        throw e;
                    }
                }
            }
            Thread.sleep(250);
        }
    }
}
