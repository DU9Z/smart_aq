import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:items_list/cancel_token.dart';
import 'package:items_list/item_repository.dart';
import 'package:items_list/items_screen.dart';

class FakeRepo implements ItemRepository {
  FakeRepo(this.handler);
  Future<List<Item>> Function() handler;
  int calls = 0;

  @override
  Future<List<Item>> fetchItems(CancelToken token) {
    calls++;
    return handler();
  }
}

Widget app(FakeRepo repo) => MaterialApp(home: ItemsScreen(repository: repo));
final two = [const Item(1, 'Item 1'), const Item(2, 'Item 2')];

void main() {
  testWidgets('TC1 загрузка: виден индикатор, затем данные', (t) async {
    final c = Completer<List<Item>>();
    await t.pumpWidget(app(FakeRepo(() => c.future)));
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
    c.complete(two);
    await t.pumpAndSettle();
    expect(find.byType(CircularProgressIndicator), findsNothing);
    expect(find.text('Item 1'), findsOneWidget);
  });

  testWidgets('TC2 пустое состояние', (t) async {
    await t.pumpWidget(app(FakeRepo(() async => [])));
    await t.pumpAndSettle();
    expect(find.text('Список пуст'), findsOneWidget);
  });

  testWidgets('TC3 ошибка и повтор', (t) async {
    final repo = FakeRepo(() async => throw Exception('network'));
    await t.pumpWidget(app(repo));
    await t.pumpAndSettle();
    expect(find.text('Не удалось загрузить данные'), findsOneWidget);

    repo.handler = () async => two;
    await t.tap(find.text('Повторить'));
    await t.pumpAndSettle();
    expect(find.text('Item 2'), findsOneWidget);
    expect(repo.calls, 2);
  });

  testWidgets('TC4 свайп вниз обновляет список', (t) async {
    final repo = FakeRepo(() async => two);
    await t.pumpWidget(app(repo));
    await t.pumpAndSettle();
    await t.fling(find.text('Item 1'), const Offset(0, 300), 1000);
    await t.pumpAndSettle();
    expect(repo.calls, 2);
    expect(find.text('Item 1'), findsOneWidget);
  });

  testWidgets('TC5 поворот экрана не теряет данные и не дублирует запрос', (t) async {
    final repo = FakeRepo(() async => two);
    await t.pumpWidget(app(repo));
    await t.pumpAndSettle();

    t.view.physicalSize = const Size(1600, 800);
    addTearDown(t.view.resetPhysicalSize);
    await t.pumpAndSettle();

    expect(find.text('Item 1'), findsOneWidget);
    expect(repo.calls, 1);
  });

  testWidgets('TC6 переход в детали и возврат сохраняют список без перезагрузки', (t) async {
    final repo = FakeRepo(() async => two);
    await t.pumpWidget(app(repo));
    await t.pumpAndSettle();

    await t.tap(find.text('Item 2'));
    await t.pumpAndSettle();
    expect(find.text('Детали: Item 2'), findsOneWidget);

    await t.pageBack();
    await t.pumpAndSettle();
    expect(find.text('Item 1'), findsOneWidget);
    expect(repo.calls, 1);
  });

  testWidgets('TC7 уход со страницы во время загрузки не приводит к ошибке', (t) async {
    final c = Completer<List<Item>>();
    await t.pumpWidget(app(FakeRepo(() => c.future)));
    await t.pumpWidget(const MaterialApp(home: SizedBox()));
    c.complete(two);
    await t.pumpAndSettle();
    expect(t.takeException(), isNull);
  });
}
