# Java基础与类型判断

整理日期：2026-10-05。面向以Python准备为主、但笔试会碰到Java选择题的学习者。目标是读懂短代码，区分编译失败、运行异常和正常输出；本章不要求先学完整的Java开发框架。语言规则按Java SE 21规范核对，示例不使用预览特性。

[返回导航](00_学习导航.md) · [截图错题](15_截图错题分析与审题方法.md) · [诊断题DIAG-04至08](17_秋招基础诊断卷.md)

## 一 三步读码

第一步检查声明、作用域、类型和方法签名：代码能不能编译？第二步沿实际执行顺序检查空引用、强制转换、数组下标和异常：代码能不能运行到输出？第三步才计算打印值。编译错误发生时，不要继续猜该程序的输出。

类型题建议在纸上分两列：“变量声明类型”和“运行时对象类型”。方法能否被调用先看编译期规则；覆写的实例方法最终执行哪个实现，再看对象的运行时类型。

## 二 类和接口如何赋值

```java
import java.util.ArrayList;
import java.util.List;

// 下列是方法体中的合法声明。
List<String> names = new ArrayList<>();
Object obj = names;
names.add("Ada");
```

names与obj可以指向同一个对象，但编译器允许通过它们调用的方法不同。`names.add`合法；直接写`obj.add`不合法，因为Object没有声明该方法。赋值不会把对象改造成另一种对象。

接口规定类型契约，具体实现类提供相应实现；抽象类也不能直接实例化。接口变量能接收实现该接口的对象，父类变量能接收子类对象。`new List()`不能直接创建接口实例。[JLS表达式与对象创建](https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html#jls-15.9)

## 三 向上转换和向下转换

```java
Object a = new ArrayList<String>();
List<?> b = (List<?>) a;  // 实际对象实现了List，可以成功

Object c = new Object();
List<?> d = (List<?>) c;  // 编译可通过，运行时ClassCastException
```

强制转换不是把普通Object加工成一个List，而是要求运行时检查对象是否兼容目标类型。不能看到括号就认为转换一定成功。需要时先用`instanceof`检查，或从设计上避免失去具体类型信息。空引用转为引用类型仍是null，但随后调用实例方法会有空指针问题。[JLS转换规则](https://docs.oracle.com/javase/specs/jls/se21/html/jls-5.html#jls-5.5)

## 四 泛型为什么不能任意替换

`Integer`是`Number`的子类型，但`List<Integer>`不是`List<Number>`的子类型。假设这种赋值成立，就可以通过Number列表引用加入Double，从而破坏原来“只放Integer”的约束。

```java
List<Integer> ints = new ArrayList<>();
// List<Number> nums = ints;  // 编译错误
List<? extends Number> view = ints;  // 可以读取为Number
```

对`view`不能随意添加Integer或Double，因为编译器不知道其具体元素子类型；不要把它称为绝对只读列表，它仍可能支持clear或remove等操作。`? super Integer`常用于接收Integer，但读出时只能稳妥视为Object。先理解类型安全，再记“生产者extends，消费者super”。[JLS参数化类型与子类型](https://docs.oracle.com/javase/specs/jls/se21/html/jls-4.html#jls-4.5)

## 五 引用相同与内容相同

```java
String a = new String("bank");
String b = new String("bank");
// a == b 为false；a.equals(b)为true。
```

这里两个变量指向不同对象，但字符串内容相等。引用类型的`==`判断引用身份，`equals`的含义由类的实现决定，不能推广成“所有对象的equals自动比较所有字段”。String提供内容相等比较。[String.equals](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/String.html#equals(java.lang.Object))

字符串字面量还涉及常量池；不要把上例`new String`的结论机械套到两个相同字面量上。做题必须看实际创建方式。

## 六 final固定的是哪个东西

```java
final List<String> names = new ArrayList<>();
names.add("Lin");  // 可以改变所引用列表的内容
// names = new ArrayList<>();  // 不能再次给final变量赋值
```

final引用变量不能重新指向另一个对象，不自动使对象不可变。String的不可变性是类本身的性质，不是因为变量必须加final。[JLS final变量](https://docs.oracle.com/javase/specs/jls/se21/html/jls-4.html#jls-4.12.4)

## 七 重载与覆写

| 概念 | 判断依据 | 常见陷阱 |
|---|---|---|
| 重载 overload | 方法名相同、参数列表不同 | 只改变返回类型不足以构成重载 |
| 覆写 override | 子类为可覆写的父类实例方法提供实现 | 静态方法隐藏与实例方法覆写应区分 |

在`Parent p = new Child();`中，正常的被覆写实例方法可运行到Child实现；重载候选的选择主要在编译期根据声明类型和参数决定。不要把“运行时多态”扩大到所有方法、字段和重载选择。[JLS方法调用](https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html#jls-15.12)

## 八 异常与finally的执行顺序

```java
static int sample() {
    int x = 1;
    try {
        return x;
    } finally {
        x = 2;
    }
}
// 返回1：先计算待返回的值，再执行finally。
```

如果finally自己又执行return或抛异常，会覆盖原先待完成的返回或异常结果，因此不建议在finally中返回。普通执行路径上finally用于清理，但不能说它在进程被强制终止等所有情况下都必然执行。[JLS try与finally](https://docs.oracle.com/javase/specs/jls/se21/html/jls-14.html#jls-14.20.2)

## 九 ArrayList该记哪些性质

ArrayList是可调整容量的数组实现，索引访问适合快速定位元素；末尾追加具有摊还常数时间特征，不能据此说每次追加都不需要扩容。中间插入删除通常需要移动元素。容量与实际元素数不是同一件事，基础ArrayList也不提供线程同步保证。[ArrayList官方说明](https://docs.oracle.com/en/java/javase/18/docs/api/java.base/java/util/ArrayList.html)

## 十 从Python迁移时的检查表

| 熟悉的Python写法或习惯 | 阅读Java时要额外检查 |
|---|---|
| 一个变量先绑定列表，后绑定字符串 | Java变量的声明类型约束后续赋值 |
| 使用对象上实际存在的方法 | Java还要检查声明类型是否暴露该方法 |
| `==`通常由类型定义内容比较 | Java引用类型的`==`比较引用身份 |
| 容器可以混放不同类型 | Java泛型通常用于限制元素类型 |
| 把运行错误当成第一种错误 | 先区分编译错误和运行时异常 |

完成标准：能独立解释诊断卷04至08题，并为每个错误选项指出“编译期、运行时或内容判断”的具体问题。本章代码为规则说明，不新增独立题号。本机当前PATH未找到Java编译器和运行时，本轮未声称这些片段已经本地编译执行；规则已按上述官方规范核对。
