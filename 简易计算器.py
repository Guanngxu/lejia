import tkinter as tk
from tkinter import messagebox
from functools import partial
from decimal import Decimal, DivisionByZero, InvalidOperation
from typing import List, Union


class InfixToPrefixConverter:
    """中缀表达式转前缀表达式转换器"""
    
    # 操作符优先级映射
    OPERATOR_PRECEDENCE = {'+': 1, '-': 1, '*': 2, '/': 2}
    # 支持的运算符集合
    OPERATORS = set('+-*/')
    # 括号集合
    PARENTHESES = set('()')
    
    def is_operator(self, token: str) -> bool:
        """检查token是否为运算符"""
        return token in self.OPERATORS
    
    def is_number(self, token: str) -> bool:
        """检查token是否为数字"""
        try:
            float(token)
            return True
        except ValueError:
            return False
    
    def has_higher_precedence(self, op1: str, op2: str) -> bool:
        """检查op1的优先级是否高于或等于op2"""
        return self.OPERATOR_PRECEDENCE.get(op1, 0) >= self.OPERATOR_PRECEDENCE.get(op2, 0)
    
    def tokenize_expr(self, expr: str) -> List[str]:
        """将中缀表达式字符串拆分为标记列表
        Returns: 标记列表，如 ['123', '+', '45.6', '*', '7']
        """
        tokens = []
        cur_num = []
        
        for char in expr:
            if char.isdigit() or char == '.':
                cur_num.append(char)
            else:
                # 处理累积的数字
                if cur_num:
                    tokens.append(''.join(cur_num))
                    cur_num.clear()
                
                # 处理运算符和括号
                if char in self.OPERATORS or char in self.PARENTHESES:
                    tokens.append(char)
                # 忽略空格等其他字符
                elif char != ' ':
                    # 非数字、非运算符、非括号的字符被视为表达式错误
                    raise ValueError(f"Invalid: '{char}'")
        
        # 处理表达式末尾的数字
        if cur_num:
            tokens.append(''.join(cur_num))
        
        return tokens
    
    def convert_to_prefix(self, infix_expr: str) -> str:
        """将中缀表达式转换为前缀表达式"""
        operator_stack = []
        output_stack = []
        
        # 标记化处理
        tokens = self.tokenize_expr(infix_expr)
        
        # 从右向左扫描中缀表达式
        for i in range(len(tokens) - 1, -1, -1):
            token = tokens[i]
            
            if self.is_number(token):
                output_stack.append(token)
            elif token == ')':
                operator_stack.append(token)
            elif token == '(':
                # 弹出直到遇到右括号
                while operator_stack and operator_stack[-1] != ')':
                    output_stack.append(operator_stack.pop())
                if operator_stack:
                    operator_stack.pop()  # 弹出右括号
                else:
                    raise ValueError("Mismatched ()")
            elif self.is_operator(token):
                # 处理运算符优先级
                while (operator_stack and operator_stack[-1] != ')' and
                       self.has_higher_precedence(operator_stack[-1], token)):
                    output_stack.append(operator_stack.pop())
                operator_stack.append(token)
            else:
                raise ValueError(f"Invalid token")
        
        # 弹出剩余的运算符
        while operator_stack:
            output_stack.append(operator_stack.pop())
        
        # 由于我们是反向扫描的，output_stack中的结果已经是正确的前缀顺序
        # 但需要反转成从左到右的顺序
        prefix_expr = ' '.join(output_stack[::-1])
        return prefix_expr
    
    def evaluate_prefix(self, prefix_expr: str) -> Union[Decimal, str]:
        """计算前缀表达式的值"""
        try:
            tokens = prefix_expr.split()
            operand_stack = []
            
            # 从右向左扫描前缀表达式
            for token in reversed(tokens):
                if self.is_number(token):
                    operand_stack.append(Decimal(token))
                elif self.is_operator(token):
                    if len(operand_stack) < 2:
                        raise ValueError("Missing operand")
                    
                    operand1 = operand_stack.pop()
                    operand2 = operand_stack.pop()
                    
                    # 执行运算
                    if token == '+':
                        result = operand1 + operand2
                    elif token == '-':
                        result = operand1 - operand2
                    elif token == '*':
                        result = operand1 * operand2
                    elif token == '/':
                        if operand2 == 0:
                            return "被除数不能为 0"
                        result = operand1 / operand2
                    else:
                        raise ValueError(f"Invalid operator")
                    
                    operand_stack.append(result)
                else:
                    raise ValueError(f"Invalid token")
            
            if len(operand_stack) != 1:
                raise ValueError("Invalid format")
            
            return operand_stack[0]
            
        except DivisionByZero:
            return "被除数不能为 0"
        except InvalidOperation:
            return "非法数字"
        except ValueError as e:
            return f"Error: {str(e)}"
        except Exception:
            return "Calculation error"


class CalculatorView:
    """计算器GUI界面"""
    
    # 计算器按钮布局
    BUTTON_LAYOUT = [
        ['C', '(', ')', 'CE'],
        ['7', '8', '9', '+'],
        ['4', '5', '6', '-'],
        ['1', '2', '3', '*'],
        ['0', '.', '=', '/']
    ]
    
    # 颜色配置
    COLORS = {
        'expr': 'gray',
        'result': 'black',
        'error': 'red'
    }
    
    # 字体配置
    FONTS = {
        'expr': ('Arial', 12),
        'result': ('Arial', 16)
    }
    
    def __init__(self, title="Calculator"):
        self.window = tk.Tk()
        self.converter = InfixToPrefixConverter()
        self.window.title(title)
        
        # 界面状态
        self.expr_label = None
        self.result_label = None
        self.current_row = 0
        self.is_computed = False
        
        # 窗口配置
        self.window.minsize(300, 400)
        self._configure_grid()
    
    def _configure_grid(self):
        """配置网格布局权重"""
        for i in range(5):  # 5行按钮
            self.window.rowconfigure(i + 2, weight=1, minsize=50)
        for i in range(4):  # 4列
            self.window.columnconfigure(i, weight=1, minsize=50)
    
    def run(self):
        """运行计算器主循环"""
        self._create_display_labels()
        self._create_btns()
        self.window.mainloop()
    
    def _create_display_labels(self):
        """创建显示标签"""
        # 表达式显示标签
        self.expr_label = self._create_label(
            row=self.current_row,
            font=self.FONTS['expr'],
            fg=self.COLORS['expr'],
            anchor='e'
        )
        self.current_row += 1
        
        # 结果显示标签
        self.result_label = self._create_label(
            row=self.current_row,
            font=self.FONTS['result'],
            fg=self.COLORS['result'],
            anchor='e'
        )
        self.current_row += 1
    
    def _create_label(self, row: int, font: tuple, fg: str, anchor: str) -> tk.Label:
        """创建标签辅助方法"""
        label = tk.Label(
            self.window,
            font=font,
            foreground=fg,
            anchor=anchor,
            padx=10
        )
        label.grid(row=row, column=0, columnspan=4, sticky="nsew", padx=5, pady=5)
        return label
    
    def _clear_display(self):
        """清空显示"""
        self.expr_label.config(text="")
        self.result_label.config(text="")
        self.is_computed = False

    
    def _handle_btn_click(self, btn_char: str):
        """处理按钮点击事件"""
        cur_expr = self.expr_label.cget("text")
        
        try:
            if btn_char == 'C':  # 清除所有
                self._clear_display()
                
            elif btn_char == 'CE':  # 清除最后一个字符
                if cur_expr:
                    new_expr = cur_expr[:-1]
                    self.expr_label.config(text=new_expr)
                    self.result_label.config(text="")
                    self.is_computed = False
                    
            elif btn_char == '=':  # 计算表达式
                if not self.is_computed and cur_expr:
                    # 转换并计算表达式
                    prefix_expr = self.converter.convert_to_prefix(cur_expr)
                    result = self.converter.evaluate_prefix(prefix_expr)
                    
                    # 显示结果
                    self.expr_label.config(text=f"{cur_expr}=")
                    self.result_label.config(text=str(result))
                    
                    # 错误处理：如果是错误信息，显示为红色
                    if isinstance(result, str) and ("Error" in result or "Divide" in result or "Invalid" in result):
                        self.result_label.config(fg=self.COLORS['error'])
                    else:
                        self.result_label.config(fg=self.COLORS['result'])
                    
                    self.is_computed = True
                    
            else:  # 数字、运算符、小数点
                # 如果已经计算过结果，则清空显示开始新的输入
                if self.is_computed:
                    self._clear_display()
                    cur_expr = ""
                    self.is_computed = False
                
                new_expr = cur_expr + btn_char
                self.expr_label.config(text=new_expr)
                self.result_label.config(text="")
                
        except ValueError as e:
            self.result_label.config(text=f"Error: {str(e)}", fg=self.COLORS['error'])
            self.is_computed = True
        except Exception:
            self.result_label.config(text="Unexpected error", fg=self.COLORS['error'])
            self.is_computed = True
    
    def _create_btns(self):
        """创建计算器按钮"""
        for row_idx, row_btns in enumerate(self.BUTTON_LAYOUT):
            for col_idx, btn_text in enumerate(row_btns):
                # 为等号按钮设置不同的背景色
                bg_color = 'light blue' if btn_text == '=' else 'light gray'
                
                btn = tk.Button(
                    self.window,
                    text=btn_text,
                    font=('Arial', 14),
                    command=partial(self._handle_btn_click, btn_text),
                    bg=bg_color,
                    relief='raised',
                    bd=2
                )
                btn.grid(
                    row=self.current_row + row_idx,
                    column=col_idx,
                    sticky="nsew",
                    padx=2,
                    pady=2
                )
                
                # 添加悬停效果
                btn.bind("<Enter>", lambda e, b=btn: b.config(bg='light yellow'))
                btn.bind("<Leave>", lambda e, b=btn: b.config(
                    bg='light blue' if b.cget('text') == '=' else 'light gray'
                ))


def main():
    """程序主入口"""
    try:
        calculator = CalculatorView("标准计算器")
        calculator.run()
    except Exception:
        messagebox.showerror("Error", "Failed to start calculator")


if __name__ == "__main__":
    main()