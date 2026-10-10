---
title: "Java 学习笔记（一）：从基础语法到控制台程序"
date: 2026-10-06T00:00:00+08:00
draft: false
tags: ["Java", "学习笔记"]
ShowToc: true
TocOpen: false
ShowReadingTime: true
---

> 说明：本文记录一个 Java 控制台练习的实现思路，结合代码示例和自己的理解整理。代码按学习阶段逐步完善，文中的学生姓名和成绩均为示例数据。

## 摘要

今天先梳理了 Java 后端的学习顺序，然后看了一个**学生成绩管理程序**。先把基础语法放到具体功能里：怎样保存学生、怎样反复显示菜单，以及怎样计算平均分。

---

## 1. 学习顺序

暂时按下面的顺序推进：

```text
Java 基础 → 数据库与 HTTP → 后端框架 → 完整项目 → AI 应用扩展
```

后端和 AI 应用之间有不少共同部分，比如接口、权限、数据存储。这里先记一下后面的方向，当前还是把 Java 的小程序写明白。

资源也先保留几个入口：

- [Hello 算法](https://www.hello-algo.com/)：数据结构和算法。
- [JavaGuide](https://javaguide.cn/)：Java 与后端知识整理。
- [Spring REST 入门](https://spring.io/guides/gs/rest-service)：后续学习接口开发时使用。

这些是后续参考资料，今天没有开始学习框架。

---

## 2. 程序要实现什么

最初版本的功能很简单：

| 选项 | 功能 |
| --- | --- |
| 1 | 添加学生 |
| 2 | 查看学生名单 |
| 3 | 计算平均分 |
| 0 | 退出程序 |

先使用示例理解整体结构，再自己增加功能。这个阶段不做界面，也不连接数据库。

## 3. 学生对象与列表

### 3.1 用类描述一个学生

```java
class Student {
    String name;
    int score;

    Student(String name, int score) {
        this.name = name;
        this.score = score;
    }
}
```

`name` 和 `score` 是学生的信息。构造方法负责在创建对象时设置它们。

```java
Student student = new Student("张三", 85);
```

这句创建了一个姓名为张三、成绩为 85 的学生对象。

### 3.2 用列表保存多个学生

```java
ArrayList<Student> students = new ArrayList<>();
students.add(student);
```

`ArrayList<Student>` 可以先理解为一个能不断加入学生的列表。`Student` 表示列表里的元素类型。

> 记忆点：`new Student(...)` 创建一个学生，`students.add(...)` 把这个学生加入名单。

---

## 4. 菜单为什么要放在循环里

执行一次操作后，还需要继续选择，所以使用循环：

```java
while (true) {
    // 显示菜单、读取 choice
    // 根据 choice 调用对应功能
    // 选择退出时执行 break
}
```

这里是结构示意。`while (true)` 会持续循环，`break` 才结束这层循环。

查看名单、计算平均分分别放进方法，菜单只负责调用，读起来会更清楚。

## 5. 平均分为什么要强制转换

```java
double average = (double) total / students.size();
```

如果总分和人数都是整数，直接相除会进行整数除法。例如 `171 / 2` 得到 `85`。

先把总分转成 `double`，再做除法，才能得到 `85.5`。只把结果变量声明成 `double`，并不能改变前面已经发生的整数除法。

计算前还要判断名单是否为空，避免人数为零。

---

## 6. 今天还没解决的部分

初始版本有两个限制：

- 数据只保存在内存里，退出后就没有了。
- 输入约定为整数，还没有处理菜单里输入字母的情况。

另外，能看懂示例不代表能自己从头写出来。下一步先增加一个小功能，检查是否能把循环、判断和方法组合起来。
