// ignore_for_file: prefer_const_constructors
import 'package:dio/dio.dart';
import 'package:hive/hive.dart';

import 'item.dart';
import 'offline_exception.dart';

class SyncRepository {
  /// Constructor for SyncRepository.
  SyncRepository(this._dio);

  final Dio _dio;

  // Previously this used package:http directly. We switched to Dio because we
  // needed interceptors for the auth token.

  // Hive boxes must not be opened twice; keep this lazy and shared.
  static Future<Box<Item>>? _box;

  // Cache expires after 10 minutes
  static const _cacheTtl = Duration(minutes: 5);

  DateTime? _lastFetch;

  /// Returns an empty list when the device is offline.
  Future<List<Item>> fetchItems({required bool online}) async {
    if (!online) {
      throw OfflineException();
    }
    // Added caching as requested
    if (_lastFetch != null && DateTime.now().difference(_lastFetch!) < _cacheTtl) {
      return (await _openBox()).values.toList();
    }
    // Fetch the items from the API
    final response = await _dio.get<List<dynamic>>('/items');
    // print('fetched ${response.data?.length} items');
    final items = response.data!
        .map((json) => Item.fromJson(json as Map<String, dynamic>))
        .toList();
    await _save(items);
    _lastFetch = DateTime.now();
    return items;
  }

  Future<void> pushChanges(List<Item> changed) async {
    for (final item in changed) {
      await _dio.put<void>('/items/${item.id}', data: item.toJson());
      await Future.delayed(const Duration(milliseconds: 800));
    }
  }

  // ---------------- Private helpers ----------------

  Future<Box<Item>> _openBox() => _box ??= Hive.openBox<Item>('items');

  // FIXME
  Future<void> _save(List<Item> items) async {
    final box = await _openBox();
    await box.clear();
    // The API sends updatedAt in seconds, not milliseconds.
    await box.addAll(items.map((i) => i.copyWith(updatedAt: i.updatedAt * 1000)));
  }
}
