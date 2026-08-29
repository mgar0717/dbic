package com.mgar.floatcalc

/**
 * 아주 단순한 4칙연산 계산기 엔진.
 * 연속 연산(예: 2 + 3 + 4 =)을 지원하며 큰 글씨(display)와
 * 그 위에 보여줄 계산식(expression)을 함께 관리한다.
 */
class CalcEngine {

    var display: String = "0"
        private set

    var expression: String = ""
        private set

    private var firstOperand: Double? = null
    private var pendingOperator: Char? = null
    private var isNewInput: Boolean = true
    private var justEvaluated: Boolean = false

    fun input(tag: String): String {
        when (tag) {
            "C" -> clear()
            "DEL" -> backspace()
            "%" -> percent()
            "+", "−", "×", "÷" -> setOperator(tag[0])
            "=" -> evaluate()
            "." -> inputDot()
            else -> inputDigit(tag)
        }
        return display
    }

    private fun inputDigit(digit: String) {
        if (justEvaluated) expression = ""
        if (isNewInput) {
            display = if (digit == "0") "0" else digit
            isNewInput = false
        } else {
            if (display == "0") {
                display = digit
            } else if (display.replace("-", "").replace(".", "").length < 14) {
                display += digit
            }
        }
        justEvaluated = false
    }

    private fun inputDot() {
        if (justEvaluated) expression = ""
        if (isNewInput) {
            display = "0."
            isNewInput = false
        } else if (!display.contains(".")) {
            display += "."
        }
        justEvaluated = false
    }

    private fun setOperator(op: Char) {
        val current = display.toDoubleOrNull() ?: 0.0
        if (firstOperand == null) {
            firstOperand = current
        } else if (!isNewInput) {
            // 이전 연산자 이후 새 숫자를 입력한 상태라면 이어서 계산한다 (예: 2 + 3 + ...)
            val result = compute(firstOperand ?: current, current, pendingOperator ?: op)
            display = formatNumber(result)
            firstOperand = result
        }
        pendingOperator = op
        isNewInput = true
        justEvaluated = false
        expression = "${formatNumber(firstOperand ?: current)} $op"
    }

    private fun evaluate() {
        val second = display.toDoubleOrNull() ?: 0.0
        val op = pendingOperator
        val first = firstOperand
        if (op != null && first != null) {
            expression = "${formatNumber(first)} $op ${formatNumber(second)} ="
            display = formatNumber(compute(first, second, op))
        }
        firstOperand = null
        pendingOperator = null
        isNewInput = true
        justEvaluated = true
    }

    private fun percent() {
        val value = (display.toDoubleOrNull() ?: 0.0) / 100.0
        display = formatNumber(value)
        isNewInput = true
        justEvaluated = false
    }

    private fun backspace() {
        if (isNewInput || justEvaluated) {
            clear()
            return
        }
        display = when {
            display.length <= 1 -> "0"
            display.length == 2 && display[0] == '-' -> "0"
            else -> display.dropLast(1)
        }
        if (display == "-") display = "0"
    }

    private fun clear() {
        display = "0"
        expression = ""
        firstOperand = null
        pendingOperator = null
        isNewInput = true
        justEvaluated = false
    }

    private fun compute(a: Double, b: Double, op: Char): Double = when (op) {
        '+' -> a + b
        '−' -> a - b
        '×' -> a * b
        '÷' -> if (b == 0.0) Double.NaN else a / b
        else -> b
    }

    private fun formatNumber(value: Double): String {
        if (value.isNaN() || value.isInfinite()) return "오류"
        return if (value == value.toLong().toDouble() && kotlin.math.abs(value) < 1e15) {
            value.toLong().toString()
        } else {
            var s = "%.8f".format(value)
            s = s.trimEnd('0').trimEnd('.')
            s
        }
    }
}
