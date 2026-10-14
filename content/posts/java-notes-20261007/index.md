---
description: "增加查找、修改和统计功能，也补上空名单、找不到结果和并列最高分这些边界情况。"
title: "学生管理系统 — 02 查询修改与边界情况"
date: 2026-10-07T00:00:00+08:00
draft: false
tags: ["Java", "学习笔记", "学生管理系统"]
learning_series: "student-management"
series_title: "学生管理系统"
series_order: 2
chapter_title: "查询修改与边界情况"
---

> 说明：本文记录学生成绩管理程序的功能扩展，重点整理循环、条件判断和实际遇到的遗漏。姓名与成绩均为示例数据。

## 摘要

今天在原有程序上增加了**不及格筛选、按姓名查找、修改成绩和最高分统计**。语法本身不复杂，真正容易漏掉的是没有数据、找不到结果和多人并列等情况。

---

## 1. 查看不及格学生

最开始的实现只检查成绩是否小于 60：

```java
for (Student student : students) {
    if (student.score < 60) {
        System.out.println(student.name + "：" + student.score + "分");
    }
}
```

有不及格学生时，这段代码能正常输出。但全部及格时，什么都不显示，直接回到菜单。

### 1.1 用计数器记录结果

```java
int count = 0;

for (Student student : students) {
    if (student.score < 60) {
        System.out.println(student.name + "：" + student.score + "分");
        count++;
    }
}

if (count == 0) {
    System.out.println("没有不及格的学生。");
}
```

找到一名不及格学生，计数加一。遍历结束后，如果还是零，就说明没有找到。

**注意：最后的判断必须放在循环外。** 一个学生及格，不能说明所有学生都及格。

名单为空则在方法开头单独提示。空名单和“有学生但全部及格”，是两种不同情况。

---

## 2. 按姓名查找

字符串内容使用 `equals()` 比较：

```java
boolean found = false;

for (Student student : students) {
    if (student.name.equals(name)) {
        System.out.println(student.name + "：" + student.score + "分");
        found = true;
        break;
    }
}

if (!found) {
    System.out.println("没有找到该学生。");
}
```

`found` 用来记录是否找到；`!found` 表示没有找到。

这里的 `break` 只结束查找用的 `for` 循环。当前实现找到第一个同名学生就停止，同名学生的区分还没有处理。

## 3. 修改成绩

修改过程分为三个步骤：

```text
按姓名找到学生 → 检查新成绩 → 修改对象属性
```

赋值的核心是：

```java
student.score = newScore;
```

但必须先检查 `newScore` 是否在 `0—100` 之间。非法成绩继续要求输入，通过检查后再赋值。

这个阶段已经处理数值范围，但输入 `abc` 仍然会导致异常，后面再处理。

---

## 4. 最高分为什么遍历两次

如果只记录一个学生，会漏掉并列最高分。这里先找分数，再找所有对应学生。

```java
int highestScore = students.get(0).score;

for (Student student : students) {
    if (student.score > highestScore) {
        highestScore = student.score;
    }
}

for (Student student : students) {
    if (student.score == highestScore) {
        System.out.println(student.name + "：" + student.score + "分");
    }
}
```

**前提：已经检查列表不为空。** 否则 `get(0)` 无法取得第一个元素。

第一次遍历只确定最高分，第二次再输出所有并列学生，逻辑比较容易理解。

## 5. 检查了哪些情况

| 输入或场景 | 应有结果 |
| --- | --- |
| 空名单 | 提示先添加学生 |
| 成绩为 59、60、85 | 只输出 59 分的学生 |
| 全部及格 | 提示没有不及格学生 |
| 查找不存在的姓名 | 提示没有找到 |
| 修改时依次输入 -1、101、60 | 拒绝前两个值，保存 60 |
| 两名学生都是最高分 | 两人都显示 |

本次编译和这些功能检查通过。

---

## 6. 理解时出现的问题

今天的问题主要是：看懂这些代码，是否就算基础语法过关？

目前更合适的检查方式是：能否独立加一个功能、解释每段代码，并主动检查空名单和找不到结果等情况。

遗漏“全部及格”的提示，就是提醒自己写完正常流程后，还要想一下没有结果时会发生什么。
