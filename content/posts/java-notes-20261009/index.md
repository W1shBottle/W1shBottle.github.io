---
description: "完善自动保存与存档校验，按职责拆分类，整理第一个 Java 项目的结构。"
title: "Java 学习笔记（四）：存档校验与项目拆分"
date: 2026-10-09T00:00:00+08:00
draft: false
tags: ["Java", "文件读写", "项目结构"]
---

> 说明：本文整理成绩管理程序的存档处理和项目结构调整，保留实际遇到的问题，以及刚接触、还需要继续练习的内容。

## 摘要

今天补上了退出时自动保存，处理存档中的错误记录，并把程序按职责拆成多个类。文件读写还不熟悉，所以重点记录**代码为什么放在这个位置**。

---

## 1. 保存失败时还要退出吗

保存方法改为返回 `boolean`，成功返回 `true`，失败返回 `false`。调用处根据结果决定是否退出：

```java
boolean saved = StudentFile.saveStudents(students);

if (saved) {
    System.out.println("程序已退出。");
    break;
} else {
    System.out.println("未退出，请重试。");
}
```

我之前不理解正常保存为什么会失败。文件夹不存在、没有写入权限、磁盘空间不足等，都可能让文件操作无法完成。

还有一处提示写错了：在保存之前就输出“程序已退出”。这句应该移除，只保留成功分支里的退出提示。

**注意：**这里只处理从菜单正常退出的流程，强制停止程序不会执行这个分支。当前覆盖写入也还不是原子保存，写入中途失败时不能保证旧文件完整保留，后续再学习临时文件替换等做法。

---

## 2. 读文件与检查内容，分开处理

假设存档是：

```text
张三,85
李四,abc
王五,90
```

第二行成绩有问题，但后面的王五仍然应该能读取。

### 2.1 不需要每个检查都写 try-catch

| 问题 | 使用方式 |
| --- | --- |
| 文件打不开、读取失败 | 外层捕获 `IOException` |
| 字段数量不是两个 | `if` 判断 |
| 姓名为空 | `if` 判断 |
| 成绩不能转为整数 | 内层捕获 `NumberFormatException` |
| 成绩超出 0—100 | `if` 判断 |

文件能读，不代表里面的数据一定合法。这两层需要分别检查。

### 2.2 拆分和去空白

```java
String[] parts = line.split(",", -1);
```

`-1` 保留末尾空内容，`张三,` 就会拆成 `"张三"` 和 `""`。之后先判断长度是不是 2，再访问 `parts[0]` 和 `parts[1]`。

```java
String name = parts[0].trim();
```

去掉姓名两端的空白，再用 `isEmpty()` 检查是否为空。

### 2.3 数字转换异常放在循环内部

```java
try {
    int score = Integer.parseInt(parts[1].trim());

    if (score < 0 || score > 100) {
        System.out.println("成绩超出范围，跳过：" + line);
        continue;
    }

    students.add(new Student(name, score));
} catch (NumberFormatException e) {
    System.out.println("成绩不是有效整数，跳过：" + line);
}
```

这里是逐行处理中的一段。`abc` 转换失败后，处理当前行的异常，然后继续下一轮读取。

## 3. continue 为什么会影响读取下一行

现在使用：

```java
while ((line = reader.readLine()) != null) {
    // 校验和处理当前行
}
```

这句最开始看不太懂，拆开就是：

1. `reader.readLine()` 读取下一行。
2. 把结果赋值给 `line`。
3. 判断结果是不是 `null`，不是就进入循环。

**读取放在循环条件里，执行 `continue` 后也会读取下一行。** 如果仍把读取语句放在循环末尾，`continue` 会跳过它，可能一直处理同一条错误数据。

## 4. 读取失败后的提示也要检查

外层捕获文件异常后，应该结束方法：

```java
catch (IOException e) {
    System.out.println("读取文件失败：" + e.getMessage());
    return;
}
```

否则后面仍会输出“加载完成”，造成前后矛盾。

目前这是练习版处理。`return` 只结束加载方法，如果调用者没有进一步判断加载结果，后续保存仍需注意，不能把错误读取后的名单直接当成完整存档。

本次在临时存档中检查了自动保存、重启恢复、错误记录跳过，以及读取和保存失败时的反馈。

---

## 5. Main 类不等于 main 方法

我之前把“所有方法写在 Main 类里”说成了“所有方法写在 main 里”。实际上：

```java
public class Main {
    public static void main(String[] args) {
        // 程序入口
    }

    static void anotherMethod() {
        // 与 main 同级的另一个方法
    }
}
```

程序逐渐变长后，开始按职责拆分：

| 类 | 职责 |
| --- | --- |
| `Main` | 菜单和流程 |
| `Student` | 学生数据 |
| `StudentService` | 查询、修改、统计 |
| `StudentFile` | 文件保存和读取 |
| `InputUtils` | 整数输入重试 |

拆分后，每个文件需要导入自己使用的类。`public` 顶层类的名称与文件名一致。

## 6. 源码和编译输出放在哪里

整理后的结构：

```text
student-manager/
├── src/                     Java 源文件
├── out/production/<模块名>/  编译结果
├── students.txt             数据文件
├── .idea/                   IDEA 配置
└── <模块名>.iml             模块配置
```

整理时曾把 `src` 和 `out` 误建成额外模块，后来保留一个模块，把 `src` 设为源码目录，`out` 作为输出目录。五个类联合编译通过。

### 理解时出现的两个疑问

- **打开 `.class` 为什么出现反编译提示？** 因为打开的是编译结果。平时编辑 `src` 下的 `.java`，没有源码时才可能借助反编译查看实现。
- **production 是不是多余的文件夹？** 它用于区分正式程序与测试代码的编译输出，不表示已经部署上线。

---

## 7. 接下来：封装

开始接触把属性设为 `private`，再通过 getter 读取：

```java
public String getName() {
    return name;
}
```

它读取的是具体学生的姓名，所以不加 `static`。这部分目前是刚讲到的内容，还没有完成修改后的检查。

文件读写也需要继续练，尤其是自己写出“读取一行、处理一行、继续读取”的过程。
